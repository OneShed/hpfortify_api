from unittest import TestCase
import hpfortify_api
import os

class TestApi(TestCase):

    username = ''
    passwd = ''

    #datadir = os.path.join(os.getcwd(), 'data')
    #api = hpfortify_api.Api(username=username, passwd=passwd, verify_ssl=False, datadir=datadir)

    def test_create_version(self):
        pass

        version = 'test123'
        description = 'test version'
        project_version = ''

    #    if self.api.project_version_exists(project, version=version):
    #        print("SSC project {} in version {} already exists".format(project, version))

    #    elif self.api.project_version_exists(project):
    #        print("SSC project {} has no version {}, creating it".format(project, version))
    #        project_version = self.api.add_version(project, version, description)
    #    else:
    #        print("SSC project {} in version {} will be created".format(project, version))
    #        project_version = self.api.create_project_version(project, version, description)

    #    print(project_version)

    def test_delete_project(self, ):
        pass
        #self.api.delete_project_version()
