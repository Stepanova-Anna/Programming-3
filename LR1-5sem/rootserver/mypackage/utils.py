def greet(name):
    """Приветствие"""
    return f"Hello, {name} from utils module!"

def get_timestamp():
    """Возвращает временную метку"""
    import time
    return time.time()