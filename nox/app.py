import os
import logging
from typing import Any, Callable, Dict

from flask import Flask
from nox.extensions import (
    db,
    celery_app
)

logger = logging.getLogger(__name__)


def create_app() -> Flask:
    app = Flask(__name__)

    try:
        # Allow user to override our config completely
        config_module = os.environ.get("SUPERSET_CONFIG", "superset.config")
        app.config.from_object(config_module)

        app_initializer = app.config.get("APP_INITIALIZER", NoxAppInitializer)(app)
        app_initializer.init_app()

        return app

    # Make sure that bootstrap errors ALWAYS get logged
    except Exception as ex:
        logger.exception("Failed to create app")
        raise ex


class NoxAppInitializer:
    def __init__(self, app: Flask) -> None:
        super().__init__()

        self.flask_app = app
        self.config = app.config
        self.manifest: Dict[Any, Any] = {}

    def pre_init(self) -> None:
        """
        Called before all other init tasks are complete
        """
        wtforms_json.init()

        if not os.path.exists(self.config["DATA_DIR"]):
            os.makedirs(self.config["DATA_DIR"])

    def post_init(self) -> None:
        """
        Called after any other init tasks
        """

    def configure_celery(self) -> None:
        celery_app.config_from_object(self.config["CELERY_CONFIG"])
        celery_app.set_default()
        flask_app = self.flask_app

        # Here, we want to ensure that every call into Celery task has an app context
        # setup properly
        task_base = celery_app.Task

        class AppContextTask(task_base):  # type: ignore
            # pylint: disable=too-few-public-methods
            abstract = True

            # Grab each call into the task and set up an app context
            def __call__(self, *args: Any, **kwargs: Any) -> Any:
                with flask_app.app_context():  # type: ignore
                    return task_base.__call__(self, *args, **kwargs)

        celery_app.Task = AppContextTask

    def init_views(self) -> None:
        pass

    def init_app(self) -> None:
        """
        Main entry point which will delegate to other methods in
        order to fully init the app
        """
        self.pre_init()
        # Configuration of logging must be done first to apply the formatter properly
        self.configure_logging()
        self.setup_db()
        self.configure_celery()

        self.post_init()

    def setup_db(self) -> None:
        db.init_app(self.flask_app)
