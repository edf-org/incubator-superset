#!/bin/bash
FLASK_APP=supersetp FLASK_ENV=development superset/bin/superset run -p 8088 --with-threads --reload --debugger --host=0.0.0.0
