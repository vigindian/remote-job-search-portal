help:
	echo "build: build docker image\npod_debug: debug pod"
build:
	docker build -t flask-remotejobs .

pod_debug:
	echo "kubectl exec -it <podname> --namespace <namespace> -- bash"
	echo "Example: kubectl exec -it remotejobs-deployment-8686f9689-mflnq -- bash"
