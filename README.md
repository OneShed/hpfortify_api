# hpfortify_api
Wrapper for the SSC API of version 1.0</br>
https://hpfortify.dwain.infra/ssc/html/docs/docs.html#/overview/

## Example

### Create the instance:
```
import hpfortify_api

username=xxx
passwd=xxx

# json templates stored here
datadir='/local/git/hpfortify_api/data'

api = hpfortify_api.Api(username=username, passwd=password, verify_ssl=False, datadir=datadir)
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
	# Add new version to the project
        api.add_version(project, version, 'description123')

else:
	# Create new project on a given version
        print( "Project {} in version {} will be created".format(project, version))
        api.create_project_version(project, version, description)
```

### Delete version of a project.
```
if( api.project_version_exists(project, version)):
	api.delete_project_version(project, version)
else:
	print("Project {} of version {} does not exist".format(project,version))
```

### Get the findings on all versions of the project
```
findings_json = api.get_findings(project)
api.json_pprint(findings_json)

{
    "AID026_Vestima_IFRD_UNIX": {
        "DEV": {
            "Low": 438,
            "Medium": 0,
            "Critical": 1,
            "High": 444,
	    "date": "2018-02-19T20:30:42"
        },
        "Release": {
            "Low": 438,
            "Medium": 0,
            "Critical": 1,
            "High": 444,
	    "date": "2018-02-19T20:45:34"
        }
    }
}

```

## Limitations
1./With the curent API, I am not able to assign the LDAP group to the new project version</br>
This means it is only readable by the account which had created it.</br>
Although limitation for our CI, we can always export a PDF report to the user as a workaround.

## Wiki (IFS related)
https://github.deutsche-boerse.de/dev/hpfortify_api/wiki
