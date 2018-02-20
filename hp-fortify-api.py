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

class Api(object):

    _sscapi = 'https://10.139.54.250/ssc/api/v1'

    _username = None
    _passwd = None
    verify_ssl = False

    def __init__(self, username=None, passwd=None, token=None, verify_ssl=False):

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
            print(req.text)
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
                print('Cannot parse JSON response')

        except requests.exceptions.RequestException as e:
            print("Error processing the response {}".format(e.message))

    # Return array of active SSC projects in format 'project - version'
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

    def project_version_exists(self, project, version):
        print('todo')

    # Return the token ID
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

    # Return ID of template (given by name)
    def get_issue_template_id(self, project_template_name=None):
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

    # Return the JSON payload for project creation
    def _version_payload(self, project_name, version_name, description, issue_template_id):

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
        #json_application_version['project']['id'] =
        json_application_version['description'] = description
        json_application_version['project']['name'] = project_name
        json_application_version['project']['description'] = description
        json_application_version['project']['issueTemplateId'] = issue_template_id
        json_application_version['issueTemplateId'] = issue_template_id

        return json.dumps(json_application_version)

   # Create project
    def create_project_version(self, project_name, version_name, issue_template_name, description):

        template_id = self.get_issue_template_id(project_template_name=issue_template_name)
        url = self._sscapi + '/projectVersions'

        payload = self._version_payload(
                project_name = project_name,
                version_name = version_name,
                issue_template_id = template_id,
                description = description
                )

        ret = self._request( method='POST', url=url, data=payload)
        return ret['data']['id']

    # Configure the project
    def populate_project_data(self, project_id):

        project_id = str(project_id)
        url = self._sscapi + '/bulk'

        # serialize json read from file
        data_file = os.path.join(os.getcwd(), 'data/payload')
        json_template=open(data_file).read()
        json_str = json_template.replace('{{api}}', self._sscapi)
        json_str = json_str.replace('{{project_id}}', project_id)
        str_json = json.loads( json_str )
        payload=json.dumps(str_json)

        ret = self._request( method='POST', url=url, data=payload)
        print('Project {} populated'.format(project_id))

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

def main():

if __name__ == "__main__":
    main()
