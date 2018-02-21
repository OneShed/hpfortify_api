#!/usr/bin/env python3

"""
API documentation:
    https://hpfortify.dwain.infra/ssc/html/docs/docs.html#/overview/

Create application version example:
    https://community.softwaregrp.com/t5/Fortify-Discussions/How-to-create-application-in-SSC-with-REST-API/td-p/1553209
    """

import requests
import logging
import json
import os
import sys
import pdb
import pprint
import traceback
import getpass

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Api(object):

    _sscapi = 'https://10.139.54.250/ssc/api/v1'
    verify_ssl = False

    _issue_template_default = 'DBG Risk Template'

    _username = None
    _passwd = None
    _issue_template_id = None

    def __init__(self, username=None, passwd=None, token=None, verify_ssl=False, issue_template=None):

        self._username = username
        self._passwd = passwd
        self.verify_ssl = verify_ssl
        self.token = token

        if username is not None:
            self.auth_type = 'basic'
        elif token is not None:
            self.auth_type = 'token'
        else:
            self.auth_type = 'unauthenticated'

        if issue_template:
            self._issue_template_id = self._get_issue_template_id(self.issue_template)
        else:
            self._issue_template_id = self._get_issue_template_id(self._issue_template_default)

    def _request(self, method, url=None, params=None, headers=None, data=''):

        if not headers:
            headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

        try:
            if self.auth_type == 'basic':
                req = requests.request(method=method,
                        url=url,
                        params=params, headers=headers,
                        data=data, verify=self.verify_ssl,
                        auth=(self._username, self._passwd))

            elif self.auth_type == 'token':
                req = requests.request(method=method,
                        url=url,
                        params=params, headers=headers,
                        data=data, verify=self.verify_ssl,
                        auth=FortifyTokenAuth(self.token))
            else:
                req = requests.request(method=method, url=url,
                        params=params, headers=headers,
                        data=payload, verify=self.verify_ssl)

                # raise an HTTPError if the HTTP request returned an unsuccessful
            #print(req.text)
            req.raise_for_status()

            response_code = req.status_code
            if response_code // 100 != 2:
                sys.exit("Response code {}".format(response_code))

            try:
                data = req.json()
                return( data )
            except ValueError:  # Return data is not JSON => return raw
                return req.content
            except:
                sys.exit('Cannot parse JSON response')

        except requests.exceptions.RequestException as e:
            sys.exit("Error processing the response {}".format(e.message))

    # Return pretty list of active SSC projects in the format 'project - version'
    def get_project_versions(self, substr=None, sort=False):  # {{{

        projects = list()
        url=self._sscapi + '/projectVersions?start=-1&limit=-1'

        req = self._request(method='GET', url=url )

        data = req['data']
        for job in data:
            nam = job['project']['name']
            version = job['name']

            if substr != None:
                if nam != None and substr in nam:
                    projects.append("%s - %s" % (nam, version))

            else:
                projects.append("%s - %s" % (nam, version))

        if sort:
            return sorted(self.uniq(projects))
        else:
            return self.uniq(projects)
    # }}}

    # Return a dict of all SSC jobs
    def _get_jobs(self):

        projects = list()
        url=self._sscapi + '/projectVersions?start=-1&limit=-1'

        req = self._request(method='GET', url=url )

        data = req['data']
        return data

    def _get_version_id(self, project_name):
        jobs=self._get_jobs()
        for job in jobs:
            if project_name in job['project']['name']:
                return job['project']['id']

    # Return True if the pair project - version exists, False otherwise
    def project_version_exists(self, project, version=None):

        project_versions = self.get_project_versions()

        if version:
            if "{} - {}".format(project, version) in project_versions:
                return True
            else:
                return False
        else:
            if any([s.startswith(project) for s in project_versions]):
                return True
            else:
                return False

    # Return the token ID (auth by user/password needed)
    # default ttl is one day, change via option might not be supported by SSC
    def get_token(self, token_type=None, ttl=None):

        url = os.path.join(self._sscapi, 'auth/token?' )

        if token_type is not None:
            url = url + 'token=' + str(token_type) + '&'
        if ttl is not None:
            url = url + 'ttl=' + str(ttl)

        req = self._request(method='GET', url=url)

        try:
            token = req['data']['token']
            return token
        except KeyError:
            print('No token found')

    # Return the ID of a template given by the name
    def _get_issue_template_id(self, project_template_name=None):
        """
        get the template id of a given template name
        e.g. 'DBG Risk Template' -> XXX-XXX-XXX-XXX
        """

        url = self._sscapi + "/issueTemplates" \
                + "?limit=1&fields=q=id:\"" \
                + project_template_name + "\""

        issue_template = self._request(method='GET', url=url)
        issue_template_id = issue_template['data'][0]['_href']
        id = issue_template_id.rsplit('/', 1)[1]

        return id

    # Return the JSON payload to be used for the project creation
    def _version_payload(self, project_name, version_name, description):

        json_application_version = dict(
                name='',			# Release
                description='',			# Production version
                active=True,
                committed=True,
                issueTemplateId='',		# 21218228-4062-4891-b126-477750115c61
                project={
                    'name': '',  		# AID026_Vestima_IFRD_UNIX
                    'description': '',  	# IFRD Scheduled pipeline
                    'issueTemplateId': '', 	# 21218228-4062-4891-b126-477750115c61
                    }
                )

        json_application_version['name'] = version_name
        json_application_version['description'] = description
        json_application_version['project']['name'] = project_name
        json_application_version['project']['description'] = description
        json_application_version['project']['issueTemplateId'] = self._issue_template_id
        json_application_version['issueTemplateId'] = self._issue_template_id

        return json.dumps(json_application_version)

    # Create (add) new vesion to already existing project
    def add_version(self, project_name, version_name, description):

        project_id = self._get_version_id(project_name)

        url = self._sscapi + "/projects/{}/versions".format(project_id)

        payload = dict(
             name=version_name,
             description=description,
             issueTemplateId=self._issue_template_id,
             active=True,
             committed=True
             #owner=owner,
             #masterAttrGuid=masteratrrguid,
         )

        payload = json.dumps(payload)

        ret = self._request( method='POST', url=url, data=payload)
        version_id =  ret['data']['id']

        self._configure_project_version(version_id)

   # Create the project - version pair
    def create_project_version(self, project_name, version_name, description):

        url = self._sscapi + '/projectVersions'

        payload = self._version_payload(
                project_name = project_name,
                version_name = version_name,
                description = description
                )

        ret = self._request( method='POST', url=url, data=payload)
        version_id = ret['data']['id']

        self._configure_project_version(version_id)

    # Configure the project (created by the method create_project_version() )
    def _configure_project_version(self, project_id):

        project_id = str(project_id)
        url = self._sscapi + '/bulk'

        # serialize the json which was read from file, TODO: move it to here
        data_file = os.path.join(os.getcwd(), 'data/payload')
        json_template=open(data_file).read()
        json_str = json_template.replace('{{api}}', self._sscapi)
        json_str = json_str.replace('{{project_id}}', project_id)

        str_json = json.loads( json_str )
        payload=json.dumps(str_json)

        ret = self._request( method='POST', url=url, data=payload)

    def json_pprint(self, dict=dict):
        jsond = json.dumps(dict, indent=4, sort_keys=False)
        print( jsond )

    def uniq(self, arr):
        uniq = list()
        uniq = [x for x in arr if x not in uniq and (uniq.append(x) or True)]
        return uniq

class FortifyTokenAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers['Authorization'] = 'FortifyToken ' + self.token
        return r
