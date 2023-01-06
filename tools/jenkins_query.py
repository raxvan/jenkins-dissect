
import os
import sys
import json
import argparse
import requests
from urllib import parse as urlparse


def typeof(instance, typename):
	class_name = instance.get("_class", None)
	return class_name == typename

def query_job_data(jk_server_addr, job_name):
	api_url = urlparse.urljoin(jk_server_addr,f"job/{job_name}/api/json")
	return requests.get(api_url).json()

def query_last_successful_data(job_info):
	url = job_info['lastSuccessfulBuild']['url']
	api_url = urlparse.urljoin(url,"api/json")
	return requests.get(api_url).json()


def main_latest_successfull_build(args):
	job_info = query_job_data(args.jenkins_host, args.job_name)
	latest_job_data = query_last_successful_data(job_info)

	job_name_upper = args.job_name.upper()
	f = open(f"{args.job_name}.sh", "w")
	f.write("#!/bin/bash\n")

	f.write("#METADATA:\n")
	f.write("export {0}_BUILD_NUMBER={1}\n".format(job_name_upper,latest_job_data['number']))
	for b in latest_job_data['actions']:
		if typeof(b,"hudson.plugins.git.util.BuildData"):
			f.write("export {0}_REVISION={1}\n".format(job_name_upper,b['lastBuiltRevision']["SHA1"]))
			break;

	f.write("#ARTIFACTS:\n")
	artifact_index = 0
	for a in latest_job_data['artifacts']:

		f.write("export {0}_ARTIFACT{1}={2}\n".format(
			job_name_upper,
			artifact_index,
			urlparse.urljoin(urlparse.urljoin(latest_job_data['url'],"artifact/"), a['relativePath'])
		))
		artifact_index += 1

	f.close()

def main(args):
	acc = args.action
	if acc == "latest":
		main_latest_successfull_build(args)


if __name__ == "__main__":
	user_arguments = sys.argv[1:]

	parser = argparse.ArgumentParser()
	parser.add_argument('jenkins_host', default=None, help='Url to jenkins host')

	subparsers = parser.add_subparsers(description='Actions:')
	#subparsers.required = True
	#^ this is required but there is a bug in 3.8.5

	latest_parser = subparsers.add_parser('latest', description='Get latest Successful build info.')
	latest_parser.set_defaults(action='latest')
	latest_parser.add_argument('job_name', default=None, help='The name of the package to install, see "list" command.')

	args = parser.parse_args(user_arguments)
	main(args)
