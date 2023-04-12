from collections import namedtuple
import numpy as np
from Visa_Project.logger import logging
from Visa_Project.exception import CustomException
import os,sys
import yaml
import importlib
from typing import List


GRID_SEARCH_KEY = 'grid_search'
MODULE_KEY = 'module'
CLASS_KEY = 'class'
PARAM_KEY = 'params'
MODEL_SELECTION_KEY = 'model_selection'
SEARCH_PARAM_GRID_KEY = 'search_param_grid'

#model serial number need to be discussed

InitializedModelDetail = namedtuple("InitializedModelDetail",["model_serial_number",
                                                              "model",
                                                              "param_grid_search",
                                                              "model_name"])

GridSearchBestModel = namedtuple("GridSearchBestModel",["model_serial_number",
                                                        "model",
                                                        "best_model",
                                                        "best_parameters",
                                                        "best_score"])

BestModel = namedtuple("BestModel",["model_serial_number",
                                    "model",
                                    "best_model",
                                    "best_parameters",
                                    "best_scores"])

MetricInfoArtifact = namedtuple("MetricInfoArtifact",["model_name","model_object","train_f1","test_f1","train_accuracy",
                                                      "test_accuracy","model_accuracy","index_number"])





class ModelFactory:
    def __init__(self,model_config_path: str = None):
        try:
            self.config: dict = ModelFactory.read_params(model_config_path)

            self.grid_search_cv_module: str = self.config[GRID_SEARCH_KEY][MODULE_KEY]
            self.grid_search_class_name: str = self.config[GRID_SEARCH_KEY][CLASS_KEY]
            self.grid_search_property_data: dict = dict(self.config[MODEL_SELECTION_KEY])

            self.models_initialization_config: dict = dict(self.config[MODEL_SELECTION_KEY])

            self.initialized_model_list = None
            self.grid_searched_best_model_list = None

        except Exception as e:
            raise CustomException(e,sys) from e
        
    @staticmethod
    def update_property_of_class(instance_ref: object, property_data: dict):
        try:
            if not isinstance(property_data,dict):
                raise Exception("property_data parameter required to dictonary")
            print(property_data)
            for key, value in property_data.items():
                logging.info(f"Executing:$ {str(instance_ref)}.{key}={value}")
                setattr(instance_ref,key,value)
            return instance_ref
        
        except Exception as e:
            raise CustomException(e,sys) from e
        
    def read_params(config_path: str)-> dict:
        try:
            with open(config_path) as yaml_file:
                config: dict = yaml.safe_load(yaml_file)
            return config
        except Exception as e:
            raise CustomException(e,sys) from e
        
    #we are defining the class to call our model file random forest and KNN
    @staticmethod
    def class_for_name(module_name: str, class_name: str):
        try:
            #load the module, will raise ImportError if module cannot be loaded
            module = importlib.import_module(module_name)
            # get the class, will raise AttributeError if class cannot be fount
            logging.info(f"Executing command: from {module} import {class_name}")
            class_ref = getattr(module, class_name)
            return class_ref
        except Exception as e:
            raise CustomException(e,sys)
        
    def execute_grid_search_operation(self,initialized_model: InitializedModelDetail,input_feature,
                                      output_feature) -> GridSearchBestModel:
        try:
            grid_search_cv_ref = ModelFactory.class_for_name(module_name=self.grid_search_cv_module,
                                                             class_name= self.grid_search_class_name)
            grid_search_cv = grid_search_cv_ref(estimator = initialized_model.model,
                                                param_grid = initialized_model.param_grid_search
                                                )
            message = f'{">>"*30} f"Training {type(initialized_model.model).__name__} Started."{"<<"*30}'
            logging.info(message)
            grid_searched_best_model = GridSearchBestModel(model_serial_number=initialized_model.model_serial_number,
                                                           model = initialized_model.model,
                                                           best_model=grid_search_cv.best_estimator_,
                                                           best_parameters=grid_search_cv.best_params_,
                                                           best_score=grid_search_cv.best_score_
                                                           )
            return grid_searched_best_model

        except Exception as e:
            raise CustomException(e,sys) from e
        
    def get_initialized_model_list(self) -> List[InitializedModelDetail]:
        """
        This function will return a list of model details.
        return List[ModelDetail]
        """
        try:
            initialized_model_list = []
            for model_serial_number in self.models_initialization_config.keys():

                model_initialization_config = self.models_initialization_config[model_serial_number]
                model_obj_ref = ModelFactory.class_for_name(module_name=model_initialization_config[MODULE_KEY],
                                                            class_name=model_initialization_config[CLASS_KEY])
                model1 = model_obj_ref()

                if PARAM_KEY in model_initialization_config:
                    model_obj_property_data = dict(model_initialization_config[PARAM_KEY])
                    model1 = ModelFactory.update_property_of_class(instance_ref=model1,
                                                                   property_data=model_obj_property_data)

                param_grid_search = model_initialization_config[SEARCH_PARAM_GRID_KEY]
                model_name = f"{model_initialization_config[MODULE_KEY]}.{model_initialization_config[CLASS_KEY]}"

                model_initialization_config = InitializedModelDetail(model_serial_number=model_serial_number,
                                                                     model=model1,
                                                                     param_grid_search=param_grid_search,
                                                                     model_name=model_name)
                initialized_model_list.append(model_initialization_config)
        except Exception as e:
            raise CustomException(e,sys) from e
        
    def initiate_best_parameter_search_for_initialized_model(self, initialized_model: InitializedModelDetail,
                                                             input_feature,
                                                             output_feature) -> GridSearchBestModel:
        """
        initiate_best_model_parameter_search(): function will perform parameter search operation, and
        it will return you the best optimistic  model with the best parameter:
        estimator: Model object
        param_grid: dictionary of parameter to perform search operation
        input_feature: all input features
        output_feature: Target/Dependent features
        ================================================================================
        return: Function will return a GridSearchOperation
        """
        try:
            return self.execute_grid_search_operation(initialized_model=initialized_model,
                                                      input_feature=input_feature,
                                                      output_feature=output_feature)
        except Exception as e:
            raise CustomException(e,sys) from e
        
    def initiate_best_parameter_search_for_initialized_models(self,
                                                              initialized_model_list: List[InitializedModelDetail],
                                                              input_feature,
                                                              output_feature) -> List[GridSearchBestModel]:
        try:
            self.grid_searched_best_model_list = []
            for initialized_model_list in initialized_model_list:
                grid_searched_best_model = self.initiate_best_parameter_search_for_initialized_model(
                    initialized_model = initialized_model_list,
                    input_feature=input_feature,
                    output_feature=output_feature
                )
                self.grid_searched_best_model_list.append(grid_searched_best_model)
            return self.grid_searched_best_model_list
        except Exception as e:
            raise CustomException(e,sys) from e
        
    @staticmethod
    def get_model_detail(model_details: List[InitializedModelDetail],
                         model_serial_number: str)-> InitializedModelDetail:
        """
        This function return ModelDetail
        """
        try:
            for model_data in model_details:
                if model_data.model_serial_number == model_serial_number:
                    return model_data
        except Exception as e:
            raise CustomException(e,sys) from e
        
    @staticmethod
    def get_best_model_from_grid_searched_best_model_list(grid_searched_best_model_list: List[GridSearchBestModel],
                                                          base_accuracy=0.6
                                                          )-> BestModel:
        try:
            best_model = None
            for grid_searched_best_model in grid_searched_best_model_list:
                if base_accuracy < grid_searched_best_model.best_score:
                    logging.info(f"Acceptable model found: {grid_searched_best_model}")
                    base_accuracy = grid_searched_best_model.best_score

                    best_model = grid_searched_best_model
                if not best_model:
                    raise Exception(f"None of madel has base accuracy: {base_accuracy}")
                logging.info(f"Best model: {best_model}")
                return best_model
        except Exception as e:
            raise CustomException(e,sys) from e
        
    def get_best_model(self, X,y,base_accuracy=0.6) -> BestModel:
        try:
            logging.info("Started Initializing model from config file")
            initialized_model_list = self.get_initialized_model_list()
            logging.info(f"Initialized model: {initialized_model_list}")
            grid_searched_best_model_list = self.initiate_best_parameter_search_for_initialized_models(
                initialized_model_list=initialized_model_list,
                input_feature=X,
                output_feature=y
            )
            return ModelFactory.get_best_model_from_grid_searched_best_model_list(grid_searched_best_model_list,
                                                                                  base_accuracy=base_accuracy)
        except Exception as e:
            raise CustomException(e,sys) from e