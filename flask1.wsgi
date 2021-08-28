import sys
sys.path.insert(0,'/var/www/aws_flask/flask1')
from website import create_app #as application

application = create_app()
application.config.from_pyfile('settings.py')
