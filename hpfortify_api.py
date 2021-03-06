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

#    _sscapi = 'https://hpfortify.dwain.infra/ssc/api/v1'
    _sscapi = 'https://10.139.54.250/ssc/api/v1'
    verify_ssl = False

    _issue_template_default = 'DBG Risk Template'

    _username = None
    _passwd = None
    _issue_template_id = None
    _datadir = None

    def __init__(self, username=None, passwd=None, token=None, verify_ssl=False, issue_template=None, datadir=None):

        self._username = username
        self._passwd = passwd
        self.verify_ssl = verify_ssl
        self.token = token
        self._datadir = datadir

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

    # Get project id of a project
    def _get_project_id(self, version_name):
        jobs=self._get_jobs()
        for job in jobs:
            if version_name in job['project']['name']:
                return job['project']['id']

    # Return authEntities json
    def _get_entities(self):
        entities = list()
        url=self._sscapi + '/authEntities?start=-1&limit=-1'

        req = self._request(method='GET', url=url )

        data = req['data']
        return data

    # Return id of and entity
    def _get_auth_entity_id(self, entity):
        entities=self._get_entities()
        for ent in entities:
            if entity in ent['entityName'] :
                return ent['id']

    # Return id of a project-version
    def _get_project_version_id(self, project, version):
        jobs=self._get_jobs()
        project_id=None

        for job in jobs:
            if project in job['project']['name']:
                project_id=job['project']['id']
                break

        if project_id==None:
                raise Exception("Project {} not found".format(project))

        url = self._sscapi + "/projects/{}/versions".format(project_id)
        req = self._request(method='GET', url=url )
        data = req['data']

        for ver in data:
            if ver['name']==version:
                return ver['id']

        sys.exit("No version {} of project {} found".format(version, project))

    # Loop all issues and return json of findings of the project-version
    def get_findings(self, project_name, project_version=None):
        jobs=self._get_jobs()
        ids=list()
        severities={"Low":0, "Low_a":0, "High":0, "High_a": 0, "Medium":0, "Medium_a":0, "Critical":0, "Critical_a":0}

        out=dict(    # project
            dict()   # { version: (severities) }
        )
        ver=dict()

        for job in jobs:
            if project_name == job['project']['name']:
                version_name=job['name']

                if project_version == None or project_version == version_name:

                   id = job['currentState']['id']
                   url=self._sscapi + "/projectVersions/{}/issues/?start=-1&limit=-1".format(id)
                   issues=self._request(method='GET', url=url)

                   for data in issues['data']:
                       issue_id = data['id']

                       if( data['friority'] == 'Low'):
                           severities["Low"]+=1
                           # ignore the audited

                       if( data['friority'] == 'Medium'):
                           severities["Medium"]+=1
                           # ignore the audited

                       if( data['friority'] == 'High'):
                           severities["High"]+=1
                           # ignore the audited

                       if( data['friority'] == 'Critical'):
                           severities["Critical"]+=1
                           tag=self.get_issue_tag(issue_id)
                           if tag != None:
                               severities['Critical_a']+=1

                   # add the date
                   date = job['currentState']['lastFprUploadDate']

                   if date != None:
                       severities["date"] = date.split('.')[0]
                   else:
                       severities["date"] = 'no scan'

                   ver[version_name]=severities
                   severities={"Low":0, "Low_a":0, "High":0, "High_a": 0, "Medium":0, "Medium_a":0, "Critical":0, "Critical_a":0}

            out[project_name] = ver

        return(out)

    # Return the audit string e.g. "not an issue", null if no audit done
    def get_issue_tag(self, issue_id):

        url=self._sscapi + "/issueDetails/{}".format(issue_id)
        issues=self._request(method='GET', url=url)

        return issues['data']['primaryTag']['tagValue']


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

        project_id = self._get_project_id(project_name)

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
        print( "Added version {} to existing project {} ({})".format(version_name, project_name, version_id))

        self._assign_auth_entities(project_name,version_name)

    def _assign_auth_entities(self, project, version):
        self._assign_auth_entity(project, version, 'FORTIFY_IFS (R)', 'Group', True  )
        self._assign_auth_entity(project, version, 'FORTIFY_IFS (W)', 'Group', True  )
        self._assign_auth_entity(project, version, 'FORTIFY_IFS (S)', 'Group', True  )
        self._assign_auth_entity(project, version, 'defaultapplowner', 'User', False  )

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
        print( "Created project {} in version {} ({})".format(project_name, version_name, version_id))

        # assign users and LDAP groups
        self._assign_auth_entities(project_name, version_name)

    # Configure the project (created by the method create_project_version() )
    def _configure_project_version(self, project_id):

        project_id = str(project_id)
        url = self._sscapi + '/bulk'

        # serialize the json which was read from file, TODO: move it to here

        data_file = os.path.join(self._datadir, 'version_config.json')
        json_template=open(data_file).read()
        json_str = json_template.replace('{{api}}', self._sscapi)
        json_str = json_str.replace('{{project_id}}', project_id)

        str_json = json.loads( json_str )
        payload=json.dumps(str_json)

        ret = self._request( method='POST', url=url, data=payload)

    # Assing users (Groups) to the version
    def _assign_auth_entity(self, project_name, version, entity_name, type, is_ldap):

        # type: Group/User

        version_id = str(self._get_project_version_id(project_name, version))

        auth_entity_id = self._get_auth_entity_id(entity_name)

        url = self._sscapi+'/projectVersions/'+version_id+'/authEntities'

        if(is_ldap):
            entity_dn="{},OU=HP Fortify,OU=Appl Groups,OU=Accounts,DC=oa,DC=pnrad,DC=net".format(entity_name)
        else:
            entity_dn=""

        data_file = os.path.join(self._datadir, 'auth_entities.json')
        json_template=open(data_file).read()

        json_str = json_template.replace('{{auth_entity_name}}', entity_name)
        json_str = json_str.replace('{{auth_entity_id}}', str(auth_entity_id))
        json_str = json_str.replace('{{is_ldap}}', str(is_ldap))
        json_str = json_str.replace('{{auth_entity_dn}}', entity_dn)
        json_str = json_str.replace('{{auth_entity_type}}', type)

        str_json = json.loads( json_str )
        payload=json.dumps(str_json)

        ret = self._request( method='PUT', url=url, data=payload)
        print( "Assigned auth entity {} to the version {} of project {}".format(entity_name, version, project_name))

    def delete_project_version(self, project, version):

        project_id = self._get_project_version_id(project, version)

        url = self._sscapi + '/projectVersions/' + str(project_id)

        ret = self._request( method='DELETE', url=url)
        print( "Version of id {} deleted".format(project_id))

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
