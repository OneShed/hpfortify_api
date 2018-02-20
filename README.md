# hp-fortify-api
Wrapper for the SSC API of vrsion 1.0

## Example

# Create the instance:
api = Api(username=username, passwd=passwd, verify_ssl=False)

# Receive API token:
token = api.get_token()

# Obtain all SSC porjects of Vestima:
vestima_projects = api.get_projects(substr='Vestima', sort=True)

# Create project-version:
id = api.create_project_version(project_name, version_name, template, description)

# Setup the project-version:
api.populate_project_data(id)

# Check if project exists:
exists = api.project_version_exists()
