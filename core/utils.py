from datetime import datetime
import os

def model_directory_path(instance, filename):
    model_name = instance.__class__.__name__.lower()
    sub_folder = datetime.now().strftime("%m-%d-%Y_%H-%M-%S")
    return os.path.join(model_name, sub_folder, filename)

def model_directory_path_property(instance, filename):
    model_name = instance.__class__.__name__.lower()
    sub_folder = str(instance.employee.id)+"/"+datetime.now().strftime("%m-%d-%Y_%H-%M-%S")
    return os.path.join(model_name, sub_folder, filename)

def model_directory_path_ava(instance, filename):
    model_name = instance.__class__.__name__.lower()
    sub_folder = str(instance.id)
    return os.path.join(model_name, sub_folder, filename)

def model_directory_path_photo(instance, filename):
    model_name = instance.__class__.__name__.lower()
    sub_folder = str(instance.employee.id)
    return os.path.join(model_name, sub_folder, filename)