class CustomException(Exception):
    u""" Общий класс ошибок """
    def __init__(self, status, message):
        self.status = status
        self.message = message
        print(message)
        super().__init__(message)


class UnauthorizedError(CustomException):
    u""" Класс ошибки Не авторизован """
    def __init__(self, *args, **kwargs):
        super().__init__(status='401', message="Не авторизован!")


class NotFoundError(CustomException):
    u""" Класс ошибки Не найдено """
    def __init__(self, *args, **kwargs):
        super().__init__(status='404', message="Не найдено!")


class DeletedError(CustomException):
    u""" Класс ошибки Уже удалено """
    def __init__(self, *args, **kwargs):
        super().__init__(status='410', message="Уже удалено!")


class InternalServerError(CustomException):
    u""" Класс внутренней ошибки сервера """
    def __init__(self, *args, **kwargs):
        super().__init__(status='500', message="Внутренняя ошибка сервера!")


class ServiceUnavailableError(CustomException):
    u""" Класс ошибки Сервис недоступен """
    def __init__(self, *args, **kwargs):
        super().__init__(status='503', message="База данных недоступна!")
