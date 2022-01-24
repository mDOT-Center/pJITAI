# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from apps.home import blueprint
from flask import render_template, request
from flask_login import login_required
from jinja2 import TemplateNotFound


@blueprint.route('/index/<algo_name>')
@login_required
def index(algo_name):
    # all finalized algorithms could be accessed using this api point
    return "api code for "+algo_name


