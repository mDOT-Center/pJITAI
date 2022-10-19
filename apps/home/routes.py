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
from flask import render_template, request
from flask_login import login_required
from jinja2 import TemplateNotFound
from flask import render_template, redirect, request, url_for

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
    return render_template("projects/projects.html")

@blueprint.route('/projects/settings/<setting_type>/', methods=['GET', 'POST'])
def project_settings(setting_type):

    if setting_type=="general":
        if request.method=='POST':
            data["general"]=request.form.to_dict()
            return data
        else:
            return render_template("design/projects/general_settings.html")
    elif setting_type=="personalized_method":
        return render_template("design/projects/personalized_method.html")
    elif setting_type=="scenario":
        return render_template("design/projects/scenario.html")
    elif setting_type=="summary":
        return render_template("design/projects/summary.html")


@blueprint.route('/intervention/settings/<setting_type>', methods=['GET', 'POST'])
def intervention_settings(setting_type):
    if setting_type=="intervention_option":
        return render_template("design/intervention/intervention_option.html")
    elif setting_type=="decision_point":
        return render_template("design/intervention/ineligibility.html")
    elif setting_type=="ineligibility":
        return render_template("design/intervention/ineligibility.html")
    elif setting_type=="intervention_probability":
        return render_template("design/intervention/intervention_probability.html")
    elif setting_type=="update_point":
        return render_template("design/intervention/update_point.html")
    elif setting_type=="summary":
        return render_template("design/intervention/summary.html")

@blueprint.route('/model/settings/<setting_type>', methods=['GET', 'POST'])
def model_settings(setting_type):
    if setting_type=="proximal_outcome_attribute":
        return render_template("design/model/proximal_outcome_attribute.html")
    elif setting_type=="intercept":
        return render_template("design/model/intercept.html")
    elif setting_type=="main_treatment_effect":
        return render_template("design/model/main_treatment_effect.html")
    elif setting_type=="covariates":
        return render_template("design/model/covariates.html")
    elif setting_type=="covariate_name":
        return render_template("design/model/covariate_name.html")
    elif setting_type=="covariate_attributes":
        return render_template("design/model/covariate_attributes.html")
    elif setting_type=="covariate_main_effect":
        return render_template("design/model/covariate_main_effect.html")
    elif setting_type=="covariate_tailored_effect":
        return render_template("design/model/covariate_tailored_effect.html")
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
