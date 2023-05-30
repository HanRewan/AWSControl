import boto3
import botocore
import os
import inspect


# upload test.py bucketmatvsviat12 test.py
class ControlAWS:

    def __init__(self, region="us-east-1", ACCESS_ID="",
                 ACCESS_KEY="", UserName="MatvSviat"):
        self.User = UserName
        self.region = region
        self.ACCESS_ID = ACCESS_ID
        self.ACCESS_KEY = ACCESS_KEY
        self.s3_client = boto3.client('s3', region_name=region, aws_access_key_id=ACCESS_ID,
                                      aws_secret_access_key=ACCESS_KEY)
        self.ec2_client = boto3.client("ec2", region_name=region, aws_access_key_id=ACCESS_ID,
                                       aws_secret_access_key=ACCESS_KEY)

        self.function_dict = {
            "create_key_pair": "create_key_pair",
            "create_instance": "create_instance",
            "get_public_ip": "get_public_ip",
            "get_running_instances": "get_running_instances",
            "run_instances": "run_instances",
            "stop_instances": "stop_instances",
            "terminate_instances": "terminate_instances",
            "create_bucket": "create_bucket",
            "list_buckets": "list_buckets",
            "upload": "upload",
            "download_file": "download_file",
            "destroy_bucket": "destroy_bucket",
            "bucket_list": "bucket_list",
            "help": "help",
            "get_instances_id": "get_instances_id",
            "switch_region": "switch_region"
        }

        running = True

        while running:

            data = input("AWSControl/" + self.User + "$ ").split()

            if len(data) == 0:
                continue

            if data[0] == "exit":
                break

            if data[0] in self.function_dict:
                data[0] = self.function_dict[data[0]]
            else:
                print("Такої команди не існує. Щоб побачити перелік усіх команди введіть команду help.")
                continue

            curr_function = getattr(ControlAWS, data[0])

            for i in range(len(data)):
                if data[i].isdigit():
                    data[i] = int(data[i])

            data[0] = self

            argssign = str(inspect.signature(curr_function))
            argsstr = ""
            for i in range(len(argssign)):
                if i == 0 or i == len(argssign) - 1:
                    continue
                argsstr += argssign[i]

            args = argsstr.split(", ")

            neclen = 0
            if args[len(args) - 1] == "*args":
                neclen = len(args)
            else:
                for elem in args:
                    if not ('=' in elem):
                        neclen += 1
            if neclen > len(data):
                print("Був пропущенний один з обов'язкових аргументів функції")
                print(args)
                continue

            curr_function(*data)

    def create_key_pair(self, name):
        key_pair = self.ec2_client.create_key_pair(KeyName=name)
        private_key = key_pair["KeyMaterial"]
        with os.fdopen(os.open("tmp/aws_ec2_key.pem", os.O_WRONLY | os.O_CREAT, 0o400), "w+") as handle:
            handle.write(private_key)

    def create_instance(self, KeyName, ImageId="ami-08c40ec9ead489470", InstanceType="t2.micro"):
        instances = self.ec2_client.run_instances(
            ImageId=ImageId,
            MinCount=1,
            MaxCount=1,
            InstanceType=InstanceType,
            KeyName=KeyName
        )

        return instances["instances"][0]["instanceId"]

    def get_public_ip(self, *args):
        instances_id_list = self.get_instances_id(0)
        for id in args:
            if not id in instances_id_list:
                print("Інстанцу з одним із введених айді не існує.")
                return

        information = []
        reservations = self.ec2_client.describe_instances(InstanceIds=args).get("Reservations")

        for reservation in reservations:
            for instance in reservation['Instances']:
                information.append(instance.get("PublicIpAddress"))

        for instance in information:
            print(instance)

    def get_running_instances(self, show=1):
        information = []
        reservations = self.ec2_client.describe_instances().get("Reservations")

        for reservation in reservations:
            for instance in reservation["Instances"]:
                if instance['State']['Name'] == 'running':
                    instance_id = instance["InstanceId"]
                    instance_type = instance["InstanceType"]
                    public_ip = instance["PublicIpAddress"]
                    private_ip = instance["PrivateIpAddress"]

                    information.append([instance_id, instance_type, public_ip, private_ip])

        if show == 1:
            print("Наразі активно інстансів: " + str(len(information)))
            for instance in information:
                print(instance)

        return information

    def get_instances_id(self, show=1):
        instances_id_list = []
        reservations = self.ec2_client.describe_instances().get("Reservations")
        for reservation in reservations:
            for instance in reservation["Instances"]:
                instances_id_list.append(instance["InstanceId"])

        if show:
            for id in instances_id_list:
                print(id)

        return instances_id_list

    def run_instances(self, show, *args):
        instances_id_list = self.get_instances_id(0)
        for id in args:
            if not id in instances_id_list:
                print("Інстанцу з одним із введених айді не існує.")
                return

        response = self.ec2_client.start_instances(InstanceIds=args, DryRun=False)
        if show == 1: print(response)
        return response

    def stop_instances(self, show, *args):
        instances_id_list = self.get_instances_id(0)
        for id in args:
            if not id in instances_id_list:
                print("Інстанцу з одним із введених айді не існує.")
                return

        response = self.ec2_client.stop_instances(InstanceIds=args)
        if show == 1: print(response)
        return response

    def terminate_instances(self, show, *args):
        instances_id_list = self.get_instances_id(0)
        for id in args:
            if not id in instances_id_list:
                print("Інстанцу з одним із введених айді не існує.")
                return

        response = self.ec2_client.terminate_instances(InstanceIds=args)
        if show == 1: print(response)
        return response

    def create_bucket(self, bucket_name, show=1):
        response = self.s3_client.create_bucket(Bucket=bucket_name)
        if show == 1: print(response)
        return response

    def list_buckets(self, show=1):
        response = self.s3_client.list_buckets()
        buckets_list = []
        if show: print('Existing buckets:')
        for bucket in response['Buckets']:
            buckets_list.append(bucket["Name"])
            if show: print(f'  {bucket["Name"]}')
        return buckets_list

    def upload(self, file_name, bucket_name, s3_obj_name, show=1):
        buckets_list = self.list_buckets(0)
        if not bucket_name in buckets_list:
            print("Бакету з такою назвою не існує або ви не маєте до нього доступу.")
            return
        try:
            response = self.s3_client.upload_file(Filename=file_name, Bucket=bucket_name, Key=s3_obj_name)
        except FileNotFoundError:
            print("Такого файле не існує.")
            return
        if show == 1: print(response)
        return response

    def download_file(self, bucket_name, file_name):
        buckets_list = self.list_buckets(0)
        if not bucket_name in buckets_list:
            print("Бакету з такою назвою не існує або ви не маєте до нього доступу.")
            return

        try:
            obj = self.s3_client.get_object(
                Bucket=bucket_name,
                Key=file_name
            )
        except botocore.exceptions.ClientError:
            print("Такого файле не існує.")
            return

        try:
            with open("tmp/" + file_name, 'x') as file:
                file.write(obj['Body'])
        except FileExistsError:
            with open("tmp/" + file_name, 'w') as file:
                file.write(obj['Body'])

        return

    def destroy_bucket(self, bucket_name, show=1):
        buckets_list = self.list_buckets(0)
        if not bucket_name in buckets_list:
            print("Бакету з такою назвою не існує або ви не маєте до нього доступу.")
            return
        response = self.s3_client.delete_bucket(Bucket=bucket_name)
        if show == 1: print(response)
        return response

    def bucket_list(self, bucket_name):
        bucket = boto3.resource('s3', region_name=self.region, aws_access_key_id=self.ACCESS_ID,
                                aws_secret_access_key=self.ACCESS_KEY).Bucket(bucket_name)
        for my_bucket_object in bucket.objects.all():
            print(my_bucket_object.key)

    def help(self, command=None):
        if command is None:
            print("Перелік усіх функцій:")
            for key in self.function_dict:
                print(key)
            return

        if command in self.function_dict.keys():
            curr_function = getattr(ControlAWS, command)
            print("self: " + command)
            print("arguments: " + str(inspect.signature(curr_function)))
            return

        print("Такої команди не існує. Щоб побачити перелік усіх команди введіть команду help.")
        return

    def switch_region(self, region):
        agreement = input("Ви впевнені? [y/N]: ")
        if agreement != 'y':
            return

        regions_data = self.ec2_client.describe_regions()
        regions_list = []
        for region_data in regions_data["Regions"]:
            regions_list.append(region_data["RegionName"])

        if region in regions_list:
            self.region = region
            print("Регіон успішно змінено на " + region + '.')
            return

        print("Такого регіону не існує.")


MyControler = ControlAWS()
