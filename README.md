# hpfortify_api
Wrapper for the SSC API of vrsion 1.0</br>
https://hpfortify.dwain.infra/ssc/html/docs/docs.html#/overview/

## Example

### Create the instance:
```
import hpfortify_api

username=xxx
passwd=xxx

api = hpfortify_api.Api(username=username, passwd=password, verify_ssl=False)
```

### Receive API token to use instead of user/pass (optional):
```
token = api.get_token(ttl=90)
```

### Obtain all SSC projects (containing name AID001)
```
project='AID001XXX'

projects = api.get_project_versions(substr=project, sort=True)
```

### Create new version of the project.</br>If the project is not found, create it too.
```
version='DEV123'
description='Some description'

if api.project_version_exists(project, version=version):
        print( "Project {} in version {} already exists".format(project, version))

elif api.project_version_exists(project):
        print( "Project {} has no version {}, creating it".format(project, version))
        api.add_version(project, version, 'description123')
else:
        print( "Project {} in version {} will be created".format(project, version))
        api.create_project_version(project, version, description)
```
