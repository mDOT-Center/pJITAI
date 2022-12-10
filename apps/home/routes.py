'''
Copyright (c) 2022 University of Memphis, mDOT Center. All rights reserved. 

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
list of conditions and the following disclaimer. 

2. Redistributions in binary form must reproduce the above copyright notice,
this list of conditions and the following disclaimer in the documentation
and/or other materials provided with the distribution. 

3. Neither the name of the copyright holder nor the names of its contributors
may be used to endorse or promote products derived from this software without
specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''

from apps.home import blueprint
import copy
from flask import render_template, request
from flask_login import login_required
from jinja2 import TemplateNotFound
from flask import render_template, redirect, request, url_for
from flask_login import login_required, current_user
from apps.algorithms.models import Projects
from apps import db
from uuid import uuid4
from flask import render_template, redirect, request, url_for, session, Response
from datetime import datetime

@blueprint.route('/index')
@login_required
def index():

    return render_template('home/index.html', segment='index')


@blueprint.route('/<template>')
@login_required
def route_template(template):

    try:

        if not template.endswith('.html'):
            template += '.html'

        # Detect the current page
        segment = get_segment(request)

        # Serve the file (if exists) from app/templates/home/FILE.html
        return render_template("home/" + template, segment=segment)

    except TemplateNotFound:
        return render_template('home/page-404.html'), 404

    except:
        return render_template('home/page-500.html'), 500
data = {}
@blueprint.route('/projects')
def projects():
    return render_template("design/projects/projects.html", project_uuid=uuid4())

def get_project_details(project_uuid, user_id):
    if project_uuid:
        project_details_obj = db.session.query(Projects).filter(Projects.created_by == user_id).filter(Projects.uuid==project_uuid).first()
        if project_details_obj:
            project_details = project_details_obj.as_dict()
        else:
            project_details={}

    return project_details, project_details_obj

@blueprint.route('/projects/settings/<setting_type>/<project_uuid>', methods=['GET', 'POST'])
def project_settings(setting_type, project_uuid=None):
    user_id = 1#current_user.get_id()
    general_settings= {}

    project_details, project_details_obj = get_project_details(project_uuid, user_id)
    # if project_uuid:
    #     project_details_obj = db.session.query(Projects).filter(Projects.created_by == user_id).filter(Projects.uuid==project_uuid).first()
    #     if project_details_obj:
    #         project_details = project_details_obj.as_dict()
    #     else:
    #         project_details={}

    if project_details.get("general_settings"):
        general_settings= project_details.get("general_settings")

    if setting_type=="general":
        return render_template("design/projects/general_settings.html", segment="general_settings", general_settings = general_settings,project_uuid=project_uuid)
    elif setting_type=="personalized_method":
        if request.method=='POST':
            if project_details_obj:
                update_general_settings(request.form.to_dict(),project_details_obj)
            else:
                gdata = request.form.to_dict()
                gdata.pop("next")
                Projects(created_by=user_id,
                         uuid=project_uuid,
                         general_settings=gdata,
                         intervention_settings={},
                         model_settings={},
                         project_status=0,
                         algo_type="algorithm_type",
                         modified_on=datetime.now(),
                         created_on=datetime.now()).save()
            return render_template("design/projects/personalized_method.html", segment="general_personalized_method", general_settings = general_settings ,project_uuid=project_uuid)
        else:
            return render_template("design/projects/personalized_method.html", segment="general_personalized_method", general_settings = general_settings ,project_uuid=project_uuid)
    elif setting_type=="scenario":
        if request.method=='POST':
            update_general_settings(request.form.to_dict(),project_details_obj)
            return render_template("design/projects/scenario.html", segment="general_scenario", general_settings = general_settings,project_uuid=project_uuid)
        else:
            return render_template("design/projects/scenario.html", segment="general_scenario", general_settings = general_settings,project_uuid=project_uuid)
    elif setting_type=="summary":
        if request.method=='POST':
            update_general_settings(request.form.to_dict(),project_details_obj)
            return render_template("design/projects/summary.html", segment="general_summary", general_settings = general_settings,project_uuid=project_uuid)
        else:
            return render_template("design/projects/summary.html", segment="general_summary", general_settings = general_settings,project_uuid=project_uuid)

def update_general_settings(data,project_details_obj):
    if project_details_obj:
        gen_settings = copy.deepcopy(project_details_obj.general_settings)
        gen_settings.update(data)
        project_details_obj.general_settings = gen_settings
        db.session.commit()

def update_intervention_settings(data,project_details_obj):
    if project_details_obj:
        settings = copy.deepcopy(project_details_obj.intervention_settings)
        settings.update(data)
        project_details_obj.intervention_settings = settings
        db.session.commit()

def update_model_settings(data,project_details_obj):
    if project_details_obj:
        settings = copy.deepcopy(project_details_obj.model_settings)
        settings.update(data)
        project_details_obj.model_settings = settings
        db.session.commit()

@blueprint.route('/intervention/settings/<setting_type>/<project_uuid>', methods=['GET', 'POST'])
def intervention_settings(setting_type,project_uuid):
    user_id = 1#current_user.get_id()
    intervention_settings= {}
    decision_point_frequency_time = ['Hour', 'Day', 'Week', 'Month']
    update_duration=['Daily', 'Weekly', 'Monthly']
    project_details, project_details_obj = get_project_details(project_uuid, user_id)

    if project_details.get("intervention_settings"):
        intervention_settings= project_details.get("intervention_settings")
        conditions = {}
        for k,v in intervention_settings.items():
            if k.startswith("condition"):
                conditions[k]=v

    if request.method=='POST':
        if 'ineligibility' in request.referrer:
            for k in list(intervention_settings.keys()):
                if k.startswith("condition"):
                    intervention_settings.pop(k)
        update_intervention_settings(request.form.to_dict(),project_details_obj)

    if setting_type=="intervention_option":
        return render_template("design/intervention/intervention_option.html", segment="intervention_option", settings = intervention_settings,project_uuid=project_uuid)

    elif setting_type=="decision_point":

        return render_template("design/intervention/decision_point.html", segment="intervention_decision_point",decision_point_frequency_time=decision_point_frequency_time, settings = intervention_settings,project_uuid=project_uuid)
    elif setting_type=="ineligibility":

        return render_template("design/intervention/ineligibility.html", segment="intervention_ineligibility", conditions=conditions, settings = intervention_settings,project_uuid=project_uuid)
    elif setting_type=="intervention_probability":
        return render_template("design/intervention/intervention_probability.html", segment="intervention_probability", settings = intervention_settings,project_uuid=project_uuid)
    elif setting_type=="update_point":
        return render_template("design/intervention/update_point.html", segment="intervention_update_point", update_duration=update_duration, settings = intervention_settings,project_uuid=project_uuid)
    elif setting_type=="summary":
        return render_template("design/intervention/summary.html", segment="intervention_summary", update_duration=update_duration, conditions=conditions, decision_point_frequency_time=decision_point_frequency_time, settings = intervention_settings,project_uuid=project_uuid)

@blueprint.route('/model/settings/<setting_type>/<project_uuid>', methods=['GET', 'POST'])
def model_settings(setting_type,project_uuid):
    user_id = 1#current_user.get_id()
    model_settings= {}

    project_details, project_details_obj = get_project_details(project_uuid, user_id)

    if project_details.get("model_settings"):
        model_settings= project_details.get("model_settings")


    if request.method=='POST':
        update_model_settings(request.form.to_dict(),project_details_obj)

    if setting_type=="proximal_outcome_attribute":
        return render_template("design/model/proximal_outcome_attribute.html", segment="intervention_option", settings = model_settings,project_uuid=project_uuid)
    elif setting_type=="intercept":
        return render_template("design/model/intercept.html", segment="intervention_option", settings = model_settings,project_uuid=project_uuid)
    elif setting_type=="main_treatment_effect":
        return render_template("design/model/main_treatment_effect.html", segment="intervention_option", settings = model_settings,project_uuid=project_uuid)
    elif setting_type=="covariates":
        return render_template("design/model/covariates.html", segment="intervention_option", settings = model_settings,project_uuid=project_uuid)
    elif setting_type=="covariate_name":
        return render_template("design/model/covariate_name.html", segment="intervention_option", settings = model_settings,project_uuid=project_uuid)
    elif setting_type=="covariate_attributes":
        return render_template("design/model/covariate_attributes.html", segment="intervention_option", settings = model_settings,project_uuid=project_uuid)
    elif setting_type=="covariate_main_effect":
        return render_template("design/model/covariate_main_effect.html", segment="intervention_option", settings = model_settings,project_uuid=project_uuid)
    elif setting_type=="covariate_tailored_effect":
        return render_template("design/model/covariate_tailored_effect.html", segment="intervention_option", settings = model_settings,project_uuid=project_uuid)
    elif setting_type=="summary":
        return render_template("design/model/summary.html")
# Helper - Extract current page name from request
def get_segment(request):

    try:

        segment = request.path.split('/')[-1]

        if segment == '':
            segment = 'index'

        return segment

    except:
        return None
