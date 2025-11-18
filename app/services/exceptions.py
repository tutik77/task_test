class TaskServiceError(Exception):
    pass


class TaskNotFoundError(TaskServiceError):
    pass


class TaskConflictError(TaskServiceError):
    pass


class PublisherUnavailableError(TaskServiceError):
    pass

