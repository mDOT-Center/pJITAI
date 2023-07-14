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

import copy
from datetime import datetime
from uuid import uuid4

from flask import render_template, redirect, request
from flask_login import login_required, current_user
from sqlalchemy import desc

from apps import db
from apps.algorithms.models import Projects
from apps.home import blueprint
from apps.home.helper import get_project_details, update_general_settings, update_intervention_settings, \
    update_model_settings, update_covariates_settings, add_menu, get_project_menu_pages
from apps.home.summary_page_probability import compute_probability


@blueprint.route('/projects/<project_type>')
@login_required
def projects(project_type):
    user_id = current_user.get_id()
    data = []
    segment = "main_project_page_"
    modified_on = datetime.now()
    if not project_type or project_type == "all":
        all_projects = db.session.query(Projects).filter(Projects.created_by == user_id).order_by(
            desc(Projects.created_on)).all()
    elif project_type == "in_progress":
        segment += "in_progress"
        all_projects = db.session.query(Projects).filter(Projects.created_by == user_id).order_by(
            desc(Projects.created_on)).filter(Projects.project_status == 0).all()
    elif project_type == "finalized":
        segment += "finalized"
        all_projects = db.session.query(Projects).filter(Projects.created_by == user_id).order_by(
            desc(Projects.created_on)).filter(Projects.project_status == 1).all()

    for aproj in all_projects:
        aproj.general_settings["project_uuid"] = aproj.uuid
        aproj.general_settings["project_status"] = aproj.project_status
        aproj.general_settings["algo_type"] = aproj.algo_type
        aproj.general_settings["modified_on"] = aproj.modified_on
        aproj.general_settings["created_on"] = aproj.created_on

        data.append(aproj.general_settings)
    
    empty_msg = 'There is no project. Please click on "Add a New Project" to create a new project.'
    if segment.find('finalized') > 0:
        empty_msg = 'There is no Finalized Project. Please finalize a project.' 

    return render_template("design/projects/projects.html", project_uuid=uuid4(), data=data, segment=segment,
                           modified_on=modified_on, empty_msg = empty_msg)


@blueprint.route('/projects/delete/<project_uuid>', methods=['GET'])
@login_required
def delete_project(project_uuid):
    user_id = current_user.get_id()
    projects.query.filter(projects.created_by == user_id).filter(projects.uuid == project_uuid).delete()
    db.session.commit()
    return redirect("/projects/in_progress")


@blueprint.route('/projects/duplicate/<project_uuid>', methods=['GET'])
@login_required
def duplicate_project(project_uuid):
    user_id = current_user.get_id()
    if project_uuid=="demo-0001":
        proj = Projects.query.filter(Projects.created_by == 1).filter(Projects.uuid == project_uuid).first()
        projs = Projects.query.filter(Projects.created_by == 1)
        for p in projs:
            print(p)
        print(f'DUPLICATES {proj} user_id = {user_id}')
    else:
        proj = Projects.query.filter(Projects.created_by == user_id).filter(Projects.uuid == project_uuid).first()
        print(f'DUPLICATES {proj} user_id = {user_id}')

    if proj:
        Projects(created_by=user_id,
                 uuid=uuid4(),
                 general_settings=proj.general_settings,
                 intervention_settings=proj.intervention_settings,
                 model_settings=proj.model_settings,
                 covariates=proj.covariates,
                 project_status=0,
                 algo_type="algorithm_type",
                 modified_on=datetime.now(),
                 created_on=datetime.now()).save()
    return redirect("/projects/in_progress")

@blueprint.route('/projects/finalize/<project_uuid>', methods=['GET'])
@login_required
def mark_project_finalized(project_uuid):
    user_id = current_user.get_id()
    proj = Projects.query.filter(Projects.created_by == user_id).filter(Projects.uuid == project_uuid).first()

    if proj:
        proj.project_status = 1
        db.session.commit()

    return redirect("/projects/finalized")

@blueprint.route('/projects/settings/<setting_type>/<project_uuid>', methods=['GET', 'POST'])
@login_required
def project_settings(setting_type, project_uuid=None):
    user_id = current_user.get_id()
    general_settings = {}
    modified_on = ""

    project_details, project_details_obj = get_project_details(project_uuid, user_id)
    project_name = project_details.get("general_settings", {}).get("study_name", "")

    if project_details.get("general_settings"):
        general_settings = project_details.get("general_settings", {})
        modified_on = project_details.get("modified_on", "")

    if request.method == 'POST':
        add_menu(user_id, project_uuid, request.path)
        if project_details_obj:
            update_general_settings(request.form.to_dict(), project_details_obj)
        else:
            gdata = request.form.to_dict()

            Projects(created_by=user_id,
                     uuid=project_uuid,
                     general_settings=gdata,
                     intervention_settings={},
                     model_settings={},
                     project_status=0,
                     algo_type="algorithm_type",
                     modified_on=datetime.now(),
                     created_on=datetime.now()).save()

    all_menus = get_project_menu_pages(user_id, project_uuid)

    if not modified_on:
        modified_on = datetime.now()

    if setting_type == "general":
        return render_template("design/projects/general_settings.html", segment="general_settings", all_menus=all_menus,
                               menu_number=1, project_name=project_name, modified_on=modified_on,
                               general_settings=general_settings, project_uuid=project_uuid)
    elif setting_type == "personalized_method":
        return render_template("design/projects/personalized_method.html", segment="general_personalized_method",
                               all_menus=all_menus, menu_number=2, project_name=project_name, modified_on=modified_on,
                               general_settings=general_settings, project_uuid=project_uuid)
    elif setting_type == "scenario":
        return render_template("design/projects/scenario.html", segment="general_scenario", modified_on=modified_on,
                               all_menus=all_menus, menu_number=3, project_name=project_name,
                               general_settings=general_settings, project_uuid=project_uuid)
    elif setting_type == "summary":
        return render_template("design/projects/summary.html", segment="general_summary", modified_on=modified_on,
                               all_menus=all_menus, menu_number=4, project_name=project_name,
                               general_settings=general_settings, project_uuid=project_uuid)


@blueprint.route('/intervention/settings/<setting_type>/<project_uuid>', methods=['GET', 'POST'])
@login_required
def intervention_settings(setting_type, project_uuid):
    user_id = current_user.get_id()
    intervention_settings = {}
    modified_on = ""
    decision_point_frequency_time = ['Hour', 'Day', 'Week', 'Month']
    update_duration = ['Daily', 'Weekly', 'Monthly']
    project_details, project_details_obj = get_project_details(project_uuid, user_id)
    project_name = project_details.get("general_settings", {}).get("study_name", "")

    if project_details.get("intervention_settings"):
        intervention_settings = project_details.get("intervention_settings")
        modified_on = project_details.get("modified_on", "")
        conditions = {}
        for k, v in intervention_settings.items():
            if k.startswith("condition"):
                conditions[k] = v

    if not modified_on:
        modified_on = datetime.now()

    if request.method == 'POST':
        add_menu(user_id, project_uuid, request.path)
        if 'ineligibility' in request.referrer:
            for k in list(intervention_settings.keys()):
                if k.startswith("condition"):
                    intervention_settings.pop(k)
        update_intervention_settings(request.form.to_dict(), project_details_obj)

    all_menus = get_project_menu_pages(user_id, project_uuid)

    if setting_type == "intervention_option":
        return render_template("design/intervention/intervention_option.html", segment="intervention_option",
                               all_menus=all_menus, menu_number=5, project_name=project_name, modified_on=modified_on,
                               settings=intervention_settings, project_uuid=project_uuid)

    elif setting_type == "decision_point":

        return render_template("design/intervention/decision_point.html", segment="intervention_decision_point",
                               all_menus=all_menus, menu_number=6, project_name=project_name, modified_on=modified_on,
                               decision_point_frequency_time=decision_point_frequency_time,
                               settings=intervention_settings, project_uuid=project_uuid)
    elif setting_type == "ineligibility":

        return render_template("design/intervention/ineligibility.html", segment="intervention_decision_point",
                               all_menus=all_menus, menu_number=7, project_name=project_name, modified_on=modified_on,
                               conditions=conditions, settings=intervention_settings, project_uuid=project_uuid)
    elif setting_type == "intervention_probability":
        return render_template("design/intervention/intervention_probability.html", segment="intervention_probability",
                               all_menus=all_menus, menu_number=8, project_name=project_name, modified_on=modified_on,
                               settings=intervention_settings, project_uuid=project_uuid)
    elif setting_type == "update_point":
        return render_template("design/intervention/update_point.html", segment="intervention_update_point",
                               all_menus=all_menus, menu_number=9, project_name=project_name, modified_on=modified_on,
                               update_duration=update_duration, settings=intervention_settings,
                               project_uuid=project_uuid)
    elif setting_type == "summary":
        return render_template("design/intervention/summary.html", segment="intervention_summary", all_menus=all_menus,
                               menu_number=10, project_name=project_name, modified_on=modified_on,
                               update_duration=update_duration, conditions=conditions,
                               decision_point_frequency_time=decision_point_frequency_time,
                               settings=intervention_settings, project_uuid=project_uuid)


@blueprint.route('/model/settings/<setting_type>/<project_uuid>', methods=['GET', 'POST'])
@login_required
def model_settings(setting_type, project_uuid):
    user_id = current_user.get_id()
    model_settings = {}
    all_covariates = {}
    modified_on = ""
    all_covs = []
    tailoring_covariates = []

    project_details, project_details_obj = get_project_details(project_uuid, user_id)
    project_name = project_details.get("general_settings", {}).get("study_name", "")
    #print(f'XXXXXXXXXX {project_details}')

    # proximal_outcome_name (general settings)
    # intervention_component_name (general settings)

    if project_details.get("model_settings"):
        all_covariates = project_details.get("covariates")
        model_settings = project_details.get("model_settings")
        modified_on = project_details.get("modified_on", "")

        model_settings["proximal_outcome_name"] = project_details.get("general_settings", {}).get(
            "proximal_outcome_name")
        model_settings["intervention_component_name"] = project_details.get("general_settings", {}).get(
            "intervention_component_name")
        model_settings['noise_scale'] = 1.00
        model_settings['noise_degree_of_freedom'] = 5
        for c in all_covariates:
            print(f'model settings {all_covariates[c]}')
            all_covs.append(all_covariates[c])
            if all_covariates[c]['tailoring_variable'] == 'yes':
                tailoring_covariates.append(all_covariates[c])

    if not modified_on:
        modified_on = datetime.now()

    if request.method == 'POST':
        add_menu(user_id, project_uuid, request.path)
        update_model_settings(request.form.to_dict(), project_details_obj)

    all_menus = get_project_menu_pages(user_id, project_uuid)#@Anand - add new menu here

    if setting_type == "proximal_outcome_attribute":
        return render_template("design/model/proximal_outcome_attribute.html",
                               segment="model_proximal_outcome_attribute", all_menus=all_menus, menu_number=11,
                               project_name=project_name, modified_on=modified_on, settings=model_settings,
                               project_uuid=project_uuid,
                               all_covariates=all_covs, 
                               tailoring_covariates=tailoring_covariates, all_covariates_count=len(all_covariates), 
                               tailoring_covariates_count=len(tailoring_covariates))
    elif setting_type == "intercept":
        return render_template("design/model/intercept.html", segment="model_intercept", all_menus=all_menus,
                               menu_number=12, project_name=project_name, modified_on=modified_on,
                               settings=model_settings, project_uuid=project_uuid, 
                               all_covariates=all_covs, 
                               tailoring_covariates=tailoring_covariates, all_covariates_count=len(all_covariates), 
                               tailoring_covariates_count=len(tailoring_covariates))
    elif setting_type == "main_treatment_effect":
        return render_template("design/model/main_treatment_effect.html", segment="model_main_treatment_effect",
                               all_menus=all_menus, menu_number=13, project_name=project_name, modified_on=modified_on,
                               settings=model_settings, project_uuid=project_uuid,
                               all_covariates=all_covs, 
                               tailoring_covariates=tailoring_covariates, all_covariates_count=len(all_covariates), 
                               tailoring_covariates_count=len(tailoring_covariates))
    elif setting_type == "main_noise":#@Anand - noise page
        '''@Anand - check this menu_number = 14'''
        return render_template("design/model/main_noise.html", segment="model_main_noise",
                               all_menus=all_menus, menu_number=14 , project_name=project_name, modified_on=modified_on,
                               settings=model_settings, project_uuid=project_uuid,
                               all_covariates=all_covs, 
                               tailoring_covariates=tailoring_covariates, all_covariates_count=len(all_covariates), 
                               tailoring_covariates_count=len(tailoring_covariates))
    elif setting_type == "summary":
        print(f'XXXXX Summary {model_settings}')
        print(f'XXXXX Summaryyyyy {model_settings["proximal_outcome_name"]}')
        return render_template("design/model/summary.html", segment="model_summary", all_menus=all_menus,
                               menu_number=16, project_name=project_name, modified_on=modified_on,
                               all_covariates=all_covariates, settings=model_settings, project_uuid=project_uuid,
                               all_covs=all_covs, 
                               proximal_outcome_name = model_settings['proximal_outcome_name'],
                               tailoring_covariates=tailoring_covariates, all_covariates_count=len(all_covariates), 
                               tailoring_covariates_count=len(tailoring_covariates))



@blueprint.route('/covariates/settings/<setting_type>/<project_uuid>', methods=['GET', 'POST'])
@blueprint.route('/covariates/settings/<setting_type>/<project_uuid>/<cov_id>', methods=['GET', 'POST'])
@login_required
def covariates_settings(setting_type, project_uuid, cov_id=None):
    user_id = current_user.get_id()
    settings = {}
    modified_on = ""
    all_covariates = {}
    covariates_types = ['Binary', 'Integer', 'Continuous']
    formula = ""

    project_details, project_details_obj = get_project_details(project_uuid, user_id)
    project_name = project_details.get("general_settings", {}).get("study_name", "")

    if project_details.get("covariates"):
        modified_on = project_details.get("modified_on", "")
        all_covariates = project_details.get("covariates")
        formula = generate_formula(project_uuid=project_uuid, is_summary_page="no", add_red_note="yes", cov_id=cov_id)

        if project_details.get("covariates").get(cov_id):
            settings = project_details.get("covariates").get(cov_id)
            settings["proximal_outcome_name"] = project_details.get("general_settings", {}).get("proximal_outcome_name")
            settings["intervention_component_name"] = project_details.get("general_settings", {}).get(
                "intervention_component_name")

    if not modified_on:
        modified_on = datetime.now()

    if request.method == 'POST':
        add_menu(user_id, project_uuid, request.path)
        if "covariate_attributes" in request.referrer:
            form_data = request.form.to_dict()
            if form_data.get("covariate_type") != "Binary":
                form_data.pop("covariate_meaning_0")
                form_data.pop("covariate_meaning_1")
                project_details_obj.covariates.get(cov_id).pop("covariate_meaning_0", None)
                project_details_obj.covariates.get(cov_id).pop("covariate_meaning_1", None)
        else:
            form_data = request.form.to_dict()

        if "covariate_main_effect" in request.referrer:
            if project_details_obj.covariates.get(cov_id).get("tailoring_variable", "") == "no":
                all_covs = copy.deepcopy(project_details_obj.covariates)
                all_covs.get(cov_id).pop("interaction_coefficient_prior_mean", None)
                all_covs.get(cov_id).pop("interaction_coefficient_prior_standard_deviation", None)

                project_details_obj.covariates = all_covs
                project_details_obj.modified_on = datetime.now()
                db.session.commit()

        if cov_id:
            update_covariates_settings(form_data, project_details_obj, cov_id)
        else:
            update_model_settings(request.form.to_dict(), project_details_obj)

    all_menus = get_project_menu_pages(user_id, project_uuid)

    if setting_type == "all":
        new_uuid = uuid4()
        return render_template("design/covariates/covariates.html", segment="covariates", all_menus=all_menus,
                               menu_number=14, project_name=project_name, modified_on=modified_on,
                               all_covariates=all_covariates, settings=settings, new_uuid=new_uuid,
                               project_uuid=project_uuid, cov_id=cov_id)
    elif setting_type == "covariate_name":
        return render_template("design/covariates/covariate_name.html", segment="covariates", all_menus=all_menus,
                               menu_number=14, project_name=project_name, modified_on=modified_on, settings=settings,
                               project_uuid=project_uuid, cov_id=cov_id)
    elif setting_type == "covariate_attributes":
        return render_template("design/covariates/covariate_attributes.html", segment="covariates", all_menus=all_menus,
                               menu_number=14, project_name=project_name, modified_on=modified_on,
                               covariates_types=covariates_types, settings=settings, project_uuid=project_uuid,
                               cov_id=cov_id)
    elif setting_type == "covariate_main_effect":
        is_tailoring = project_details_obj.covariates.get(cov_id).get("tailoring_variable", "no")
        return render_template("design/covariates/covariate_main_effect.html", segment="covariates", formula=formula,
                               all_menus=all_menus, menu_number=14, project_name=project_name, modified_on=modified_on,
                               is_tailoring=is_tailoring, settings=settings, project_uuid=project_uuid, cov_id=cov_id)
    elif setting_type == "covariate_tailored_effect":
        formula = generate_formula(project_uuid=project_uuid, is_summary_page="no", add_red_note="yes", cov_id=cov_id, covariate_tailored_effect=True)

        return render_template("design/covariates/covariate_tailored_effect.html", segment="covariates",
                               formula=formula, all_menus=all_menus, menu_number=14, project_name=project_name,
                               modified_on=modified_on, settings=settings, project_uuid=project_uuid, cov_id=cov_id)
    elif setting_type == "covariate_summary":
        tal_val = project_details_obj.covariates.get(cov_id).get("tailoring_variable", "no")
        is_tailoring = True
        if tal_val == 'no':
            is_tailoring = False
        print(f'TTTTTTTTT {is_tailoring}')
        formula = generate_formula(project_uuid=project_uuid, is_summary_page="yes", add_red_note="no")
        return render_template("design/covariates/covariate_summary.html", segment="covariates", formula=formula,
                               all_menus=all_menus, menu_number=14, project_name=project_name, modified_on=modified_on,
                               all_covariates=all_covariates, covariates_types=covariates_types, settings=settings,
                               project_uuid=project_uuid, cov_id=cov_id, is_tailoring=is_tailoring)


@blueprint.route('/covariates/settings/delete/<project_uuid>/<cov_id>', methods=['GET'])
@login_required
def delete_covariate(project_uuid, cov_id=None):
    user_id = current_user.get_id()

    project_details, project_details_obj = get_project_details(project_uuid, user_id)
    covariates = copy.deepcopy(project_details.get("covariates", {}))
    if covariates.get(cov_id):
        covariates.pop(cov_id)
        project_details_obj.covariates = covariates
        project_details_obj.modified_on = datetime.now()
        db.session.commit()

    return redirect("/covariates/settings/all/" + project_uuid)


@blueprint.route('/get_probability/<project_uuid>', methods=['GET'])
#@login_required
def get_probability(project_uuid):
    user_id = current_user.get_id()
    project_details, project_details_obj = get_project_details(project_uuid, user_id)
    req_data = request.values
    print(f'get_probability called {project_uuid} {req_data}')
    tailoring_cov_data = {}
    for x in req_data:
        tailoring_cov_data[x] = req_data[x]
    print(f'computing probability for {tailoring_cov_data}')
    prob = compute_probability(project_details, tailoring_cov_data) 
    prob = round(prob, 2)
    print(f'returning NEW probability {prob}')
    # call Hsin-Yu method and get the response
    return f'{prob}%'


@blueprint.route('/configuration/<config_type>/<project_uuid>', methods=['GET', 'POST'])
@login_required
def configuration_summary(config_type, project_uuid):
    user_id = current_user.get_id()
    modified_on = ""
    settings = {}

    project_details, project_details_obj = get_project_details(project_uuid, user_id)
    settings["intervention_probability_lower_bound"] = project_details.get("intervention_settings", {}).get(
        "intervention_probability_lower_bound")
    settings["intervention_probability_upper_bound"] = project_details.get("intervention_settings", {}).get(
        "intervention_probability_upper_bound")
    all_menus = get_project_menu_pages(user_id, project_uuid)


    #test
    project_details['location_location'] = 0
    # end test

    if project_details.get("covariates"):
        modified_on = project_details.get("modified_on", "")
    # Call Hsin-Yu method here @Anand. Add a new paramenter in render summary
    if not modified_on:
        modified_on = datetime.now()
    if config_type == "summary":
        #print(f'CONFIGURATION SUMMARY {project_details}')
        prox_name = project_details.get('intervention_settings').get('intervention_option_a')
        print(f'INTERVENTION_OPTION_A {prox_name}')

        proximal_outcome_name = prox_name
        covs = project_details.get('covariates') 
        tailoring_covs_names = []
        tailoring_covs_description = []

        for cov in covs:
            #print(f"COVARIATE {covs.get(cov).get('covariate_name')} {covs.get(cov).get('tailoring_variable')}")  
            if covs.get(cov).get('tailoring_variable') == 'yes':
                cov_name = covs.get(cov).get('covariate_name')
                cov_desc = 'XXX'
                if covs.get(cov).get('covariate_type') == 'Binary':
                    cov_desc = f"Type: {covs.get(cov).get('covariate_type')} 0: {covs.get(cov).get('covariate_meaning_0')} 1: {covs.get(cov).get('covariate_meaning_1')}" 
                else:
                    cov_desc = f"Type: {covs.get(cov).get('covariate_type')} Min: {covs.get(cov).get('covariate_min_val')} Max: {covs.get(cov).get('covariate_max_val')}"
                tailoring_covs_names.append(cov_name)
                tailoring_covs_description.append(cov_desc)
        
        data_for_prob = {}
        for x in tailoring_covs_names:
            data_for_prob[x] = 0
        
        print(f'SUMMARY data for computing probability = {data_for_prob}')
        prob = compute_probability(project_details, data_for_prob) 
        prob_str = str(prob) + '%'


        return render_template("design/config_summary/summary.html", segment="configuration_summary", settings=settings,
                               project_details=project_details,
                               proximal_outcome_name=proximal_outcome_name,
                               tailoring_covs_num = len(tailoring_covs_names),
                               tailoring_covs_names = tailoring_covs_names,
                               tailoring_covs_description = tailoring_covs_description,
                               all_menus=all_menus, menu_number=16, modified_on=modified_on, project_uuid=project_uuid, probability=prob_str)
    elif config_type == "final":
        return render_template("design/config_summary/final.html", segment="configuration_final", settings=settings,
                               all_menus=all_menus, menu_number=17, modified_on=modified_on, project_uuid=project_uuid)


@blueprint.route('/pages/<page_type>', methods=['GET'])
@login_required
def static_pages(page_type):
    if page_type == "about":
        return render_template("design/static_pages/about_us.html", segment="static_pages")
    elif page_type == "faqs":
        return render_template("design/static_pages/faqs.html", segment="static_pages")
    elif page_type == "contact":
        return render_template("design/static_pages/contact_us.html", segment="static_pages")
    else:
        return "Page not found", 404


@blueprint.route('/generate_formula/<project_uuid>/<page_type>/<add_red_note>', methods=['GET', 'POST'])
@login_required
def generate_formula(project_uuid, is_summary_page, add_red_note, cov_id=None, covariate_tailored_effect=False):
    user_id = current_user.get_id()
    alphas = ""
    betas = ""

    alpha_counter, beta_counter = 1, 1
    project_details, project_details_obj = get_project_details(project_uuid, user_id)

    proximal_outcome_name = project_details.get("general_settings", {}).get("proximal_outcome_name")
    intervention_component_name = project_details.get("general_settings", {}).get("intervention_component_name")

    intercept_prior_mean = project_details.get("model_settings", {}).get("intercept_prior_mean")
    intercept_prior_standard_deviation = project_details.get("model_settings", {}).get(
        "intercept_prior_standard_deviation")
    treatment_prior_mean = project_details.get("model_settings", {}).get("treatment_prior_mean")
    treatment_prior_standard_deviation = project_details.get("model_settings", {}).get(
        "treatment_prior_standard_deviation")

    covariates = project_details.get("covariates")

    alpha_vars = f'α<sub>0</sub>~N({intercept_prior_mean}, {intercept_prior_standard_deviation}<sup>2</sup>)<br>'
    beta_vars = f'β<sub>0</sub>~N({treatment_prior_mean}, {treatment_prior_standard_deviation}<sup>2</sup>)<br>'

    for acov in reversed(covariates):
        covariates.get(acov)
        cov_vars = covariates.get(acov, {})
        name = covariates.get(acov, {}).get("covariate_name")
        is_tailoring = cov_vars.get("tailoring_variable")
        alphas += f"""<br>+ α<sub>{alpha_counter}</sub> * <span id="cov_name_span1" style="background:#888; font-size:14px;">{name}</span> """
        alpha_vars += f'α<sub>{alpha_counter}</sub>~N({cov_vars.get("main_effect_prior_mean")}, {cov_vars.get("main_effect_prior_standard_deviation")}<sup>2</sup>)<br>'
        alpha_counter += 1
        if is_tailoring == "yes":
            betas += f"""<br><span id="beta_{beta_counter}">+ β<sub>{beta_counter}</sub>* <span id="cov_name_span2" style="background:#888; font-size:14px;">{name}</span>  * <span style="background:#888; font-size:14px;"> {intervention_component_name} </span></span>"""
            beta_vars += f'β<sub>{beta_counter}</sub>~N({cov_vars.get("main_effect_prior_mean")}, {cov_vars.get("main_effect_prior_standard_deviation")}<sup>2</sup>)<br>'
            beta_counter += 1

    htmll = f"""<p class="rightsidebluetextbox">

                    <span style="background:#888; font-size:14px;">{proximal_outcome_name}</span> ~ <br>
                    α<sub>0</sub> 
                    
                    {alphas}
                    
                    <br><br>
                    + β<sub>0</sub> * <span style="background:#888; font-size:14px;"> {intervention_component_name} </span>
                                                      
                    {betas}
                    
                    <br>+ ϵ <br>
                    RED_NOTE
                    <br>
                    ALPHA_VARS 
                    BETA_VARS
                </p>"""
    if is_summary_page == "yes":
        htmll = htmll.replace("ALPHA_VARS", alpha_vars)
        htmll = htmll.replace("BETA_VARS", beta_vars)
    else:
        htmll = htmll.replace("ALPHA_VARS", "")
        htmll = htmll.replace("BETA_VARS", "")

    if add_red_note == "yes":
        cov_alpha = 1
        cov_beta = 1
        for acov in reversed(covariates):
            cov_vars = covariates.get(acov, {})
            name = covariates.get(acov, {}).get("covariate_name")
            is_tailoring = cov_vars.get("tailoring_variable")
            if cov_id == acov:
                break
            cov_alpha += 1
            if is_tailoring == "yes":
                cov_beta +=1

        if not covariate_tailored_effect: 
            htmll = htmll.replace("RED_NOTE",
                              f'α<sub>{cov_alpha}</sub>~N(<span style="color:#f65959;">μ<sub>α<sub>{cov_alpha}</sub></sub>, σ<sub>α<sub>{cov_alpha}</sub></sub></span><sup>2</sup>) <br> <span style="color:#f65959;"> We are asking for the red values.</span>')
        else:
            htmll = htmll.replace("RED_NOTE",
                              f'''β<sub>{cov_beta}</sub>~N(<span style="color:#f65959;">μ<sub>β<sub>{cov_beta}</sub></sub>, σ<sub>β<sub>{cov_beta}</sub></sub></span><sup>2</sup>) <br> <span style="color:#f65959;"> We are asking for the red values.</span>''')

    else:
        htmll = htmll.replace("RED_NOTE", "")
    return htmll
