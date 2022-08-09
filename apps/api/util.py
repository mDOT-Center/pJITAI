from datetime import datetime


def time_8601(time=datetime.now()) -> str:
    return time.astimezone().isoformat()

def get_class_object(class_path:str):
    from importlib import import_module

    module_path, class_name = class_path.rsplit('.', 1)
    module = import_module(module_path)

    return getattr(module, class_name)


