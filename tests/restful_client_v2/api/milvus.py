import json
import requests
import time
import uuid
from utils.util_log import test_log as logger
from minio import Minio
from minio.error import S3Error


def logger_request_response(response, url, tt, headers, data, str_data, str_response, method):
    if len(data) > 2000:
        data = data[:1000] + "..." + data[-1000:]
    try:
        if response.status_code == 200:
            if ('code' in response.json() and response.json()["code"] == 200) or (
                    'Code' in response.json() and response.json()["Code"] == 0):
                logger.debug(
                    f"\nmethod: {method}, \nurl: {url}, \ncost time: {tt}, \nheader: {headers}, \npayload: {str_data}, \nresponse: {str_response}")
            else:
                logger.debug(
                    f"\nmethod: {method}, \nurl: {url}, \ncost time: {tt}, \nheader: {headers}, \npayload: {data}, \nresponse: {response.text}")
        else:
            logger.debug(
                f"method: \nmethod: {method}, \nurl: {url}, \ncost time: {tt}, \nheader: {headers}, \npayload: {data}, \nresponse: {response.text}")
    except Exception as e:
        logger.debug(
            f"method: \nmethod: {method}, \nurl: {url}, \ncost time: {tt}, \nheader: {headers}, \npayload: {data}, \nresponse: {response.text}, \nerror: {e}")


class Requests:
    def __init__(self, url=None, api_key=None):
        self.url = url
        self.api_key = api_key
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
            'RequestId': str(uuid.uuid1())
        }

    def update_headers(self):
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
            'RequestId': str(uuid.uuid1())
        }
        return headers

    def post(self, url, headers=None, data=None, params=None):
        headers = headers if headers is not None else self.update_headers()
        data = json.dumps(data)
        str_data = data[:200] + '...' + data[-200:] if len(data) > 400 else data
        t0 = time.time()
        response = requests.post(url, headers=headers, data=data, params=params)
        tt = time.time() - t0
        str_response = response.text[:200] + '...' + response.text[-200:] if len(response.text) > 400 else response.text
        logger_request_response(response, url, tt, headers, data, str_data, str_response, "post")
        return response

    def get(self, url, headers=None, params=None, data=None):
        headers = headers if headers is not None else self.update_headers()
        data = json.dumps(data)
        str_data = data[:200] + '...' + data[-200:] if len(data) > 400 else data
        t0 = time.time()
        if data is None or data == "null":
            response = requests.get(url, headers=headers, params=params)
        else:
            response = requests.get(url, headers=headers, params=params, data=data)
        tt = time.time() - t0
        str_response = response.text[:200] + '...' + response.text[-200:] if len(response.text) > 400 else response.text
        logger_request_response(response, url, tt, headers, data, str_data, str_response, "get")
        return response

    def put(self, url, headers=None, data=None):
        headers = headers if headers is not None else self.update_headers()
        data = json.dumps(data)
        str_data = data[:200] + '...' + data[-200:] if len(data) > 400 else data
        t0 = time.time()
        response = requests.put(url, headers=headers, data=data)
        tt = time.time() - t0
        str_response = response.text[:200] + '...' + response.text[-200:] if len(response.text) > 400 else response.text
        logger_request_response(response, url, tt, headers, data, str_data, str_response, "put")
        return response

    def delete(self, url, headers=None, data=None):
        headers = headers if headers is not None else self.update_headers()
        data = json.dumps(data)
        str_data = data[:200] + '...' + data[-200:] if len(data) > 400 else data
        t0 = time.time()
        response = requests.delete(url, headers=headers, data=data)
        tt = time.time() - t0
        str_response = response.text[:200] + '...' + response.text[-200:] if len(response.text) > 400 else response.text
        logger_request_response(response, url, tt, headers, data, str_data, str_response, "delete")
        return response


class VectorClient(Requests):
    def __init__(self, endpoint, token):
        super().__init__(url=endpoint, api_key=token)
        self.endpoint = endpoint
        self.token = token
        self.api_key = token
        self.db_name = None
        self.headers = self.update_headers()

    def update_headers(self):
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
            'Accept-Type-Allow-Int64': "true",
            'RequestId': str(uuid.uuid1())
        }
        return headers

    def vector_search(self, payload, db_name="default", timeout=10):
        time.sleep(1)
        url = f'{self.endpoint}/v2/vectordb/entities/search'
        if self.db_name is not None:
            payload["dbName"] = self.db_name
        if db_name != "default":
            payload["dbName"] = db_name
        response = self.post(url, headers=self.update_headers(), data=payload)
        rsp = response.json()
        if "data" in rsp and len(rsp["data"]) == 0:
            t0 = time.time()
            while time.time() - t0 < timeout:
                response = self.post(url, headers=self.update_headers(), data=payload)
                rsp = response.json()
                if len(rsp["data"]) > 0:
                    break
                time.sleep(1)
            else:
                response = self.post(url, headers=self.update_headers(), data=payload)
                rsp = response.json()
                if "data" in rsp and len(rsp["data"]) == 0:
                    logger.info(f"after {timeout}s, still no data")

        return response.json()

    def vector_query(self, payload, db_name="default", timeout=10):
        time.sleep(1)
        url = f'{self.endpoint}/v2/vectordb/entities/query'
        if self.db_name is not None:
            payload["dbName"] = self.db_name
        if db_name != "default":
            payload["dbName"] = db_name
        response = self.post(url, headers=self.update_headers(), data=payload)
        rsp = response.json()
        if "data" in rsp and len(rsp["data"]) == 0:
            t0 = time.time()
            while time.time() - t0 < timeout:
                response = self.post(url, headers=self.update_headers(), data=payload)
                rsp = response.json()
                if len(rsp["data"]) > 0:
                    break
                time.sleep(1)
            else:
                response = self.post(url, headers=self.update_headers(), data=payload)
                rsp = response.json()
                if "data" in rsp and len(rsp["data"]) == 0:
                    logger.info(f"after {timeout}s, still no data")

        return response.json()

    def vector_get(self, payload, db_name="default"):
        time.sleep(1)
        url = f'{self.endpoint}/v2/vectordb/entities/get'
        if self.db_name is not None:
            payload["dbName"] = self.db_name
        if db_name != "default":
            payload["dbName"] = db_name
        response = self.post(url, headers=self.update_headers(), data=payload)
        return response.json()

    def vector_delete(self, payload, db_name="default"):
        url = f'{self.endpoint}/v2/vectordb/entities/delete'
        if self.db_name is not None:
            payload["dbName"] = self.db_name
        if db_name != "default":
            payload["dbName"] = db_name
        response = self.post(url, headers=self.update_headers(), data=payload)
        return response.json()

    def vector_insert(self, payload, db_name="default"):
        url = f'{self.endpoint}/v2/vectordb/entities/insert'
        if self.db_name is not None:
            payload["dbName"] = self.db_name
        if db_name != "default":
            payload["dbName"] = db_name
        response = self.post(url, headers=self.update_headers(), data=payload)
        return response.json()

    def vector_upsert(self, payload, db_name="default"):
        url = f'{self.endpoint}/v2/vectordb/entities/upsert'
        if self.db_name is not None:
            payload["dbName"] = self.db_name
        if db_name != "default":
            payload["dbName"] = db_name
        response = self.post(url, headers=self.update_headers(), data=payload)
        return response.json()


class CollectionClient(Requests):

    def __init__(self, endpoint, token):
        super().__init__(url=endpoint, api_key=token)
        self.endpoint = endpoint
        self.api_key = token
        self.db_name = None
        self.headers = self.update_headers()

    def update_headers(self, headers=None):
        if headers is not None:
            return headers
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
            'RequestId': str(uuid.uuid1())
        }
        return headers

    def collection_has(self, db_name="default", collection_name=None):
        url = f'{self.endpoint}/v2/vectordb/collections/has'
        if self.db_name is not None:
            db_name = self.db_name
        data = {
            "dbName": db_name,
            "collectionName": collection_name
        }
        response = self.post(url, headers=self.update_headers(), data=data)
        res = response.json()
        return res

    def collection_rename(self, payload, db_name="default"):
        url = f'{self.endpoint}/v2/vectordb/collections/rename'
        if self.db_name is not None:
            payload["dbName"] = self.db_name
        if db_name != "default":
            payload["dbName"] = db_name
        response = self.post(url, headers=self.update_headers(), data=payload)
        return response.json()

    def collection_stats(self, db_name="default", collection_name=None):
        url = f'{self.endpoint}/v2/vectordb/collections/get_stats'
        if self.db_name is not None:
            db_name = self.db_name
        data = {
            "dbName": db_name,
            "collectionName": collection_name
        }
        response = self.post(url, headers=self.update_headers(), data=data)
        res = response.json()
        return res

    def collection_load(self, db_name="default", collection_name=None):
        url = f'{self.endpoint}/v2/vectordb/collections/load'
        if self.db_name is not None:
            db_name = self.db_name
        payload = {
            "dbName": db_name,
            "collectionName": collection_name
        }
        response = self.post(url, headers=self.update_headers(), data=payload)
        res = response.json()
        return res

    def collection_release(self, db_name="default", collection_name=None):
        url = f'{self.endpoint}/v2/vectordb/collections/release'
        if self.db_name is not None:
            db_name = self.db_name
        payload = {
            "dbName": db_name,
            "collectionName": collection_name
        }
        response = self.post(url, headers=self.update_headers(), data=payload)
        res = response.json()
        return res

    def collection_load_state(self, db_name="default", collection_name=None, partition_names=None):
        url = f'{self.endpoint}/v2/vectordb/collections/get_load_state'
        if self.db_name is not None:
            db_name = self.db_name
        data = {
            "dbName": db_name,
            "collectionName": collection_name,
        }
        if partition_names is not None:
            data["partitionNames"] = partition_names
        response = self.post(url, headers=self.update_headers(), data=data)
        res = response.json()
        return res

    def collection_list(self, db_name="default"):
        url = f'{self.endpoint}/v2/vectordb/collections/list'
        params = {}
        if self.db_name is not None:
            params = {
                "dbName": self.db_name
            }
        if db_name != "default":
            params = {
                "dbName": db_name
            }
        response = self.post(url, headers=self.update_headers(), params=params)
        res = response.json()
        return res

    def collection_create(self, payload, db_name="default"):
        time.sleep(1)  # wait for collection created and in case of rate limit
        url = f'{self.endpoint}/v2/vectordb/collections/create'
        if self.db_name is not None:
            payload["dbName"] = self.db_name
        if db_name != "default":
            payload["dbName"] = db_name
        response = self.post(url, headers=self.update_headers(), data=payload)
        return response.json()

    def collection_describe(self, collection_name, db_name="default"):
        url = f'{self.endpoint}/v2/vectordb/collections/describe'
        data = {"collectionName": collection_name}
        if self.db_name is not None:
            data = {
                "collectionName": collection_name,
                "dbName": self.db_name
            }
        if db_name != "default":
            data = {
                "collectionName": collection_name,
                "dbName": db_name
            }
        response = self.post(url, headers=self.update_headers(), data=data)
        return response.json()

    def collection_drop(self, payload, db_name="default"):
        time.sleep(1)  # wait for collection drop and in case of rate limit
        url = f'{self.endpoint}/v2/vectordb/collections/drop'
        if self.db_name is not None:
            payload["dbName"] = self.db_name
        if db_name != "default":
            payload["dbName"] = db_name
        response = self.post(url, headers=self.update_headers(), data=payload)
        return response.json()


class PartitionClient(Requests):

    def __init__(self, endpoint, token):
        super().__init__(url=endpoint, api_key=token)
        self.endpoint = endpoint
        self.api_key = token
        self.db_name = None
        self.headers = self.update_headers()

    def update_headers(self):
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
            'RequestId': str(uuid.uuid1())
        }
        return headers

    def partition_list(self, db_name="default", collection_name=None):
        url = f'{self.endpoint}/v2/vectordb/partitions/list'
        data = {
            "collectionName": collection_name
        }
        if self.db_name is not None:
            data = {
                "dbName": self.db_name,
                "collectionName": collection_name
            }
        if db_name != "default":
            data = {
                "dbName": db_name,
                "collectionName": collection_name
            }
        response = self.post(url, headers=self.update_headers(), data=data)
        res = response.json()
        return res

    def partition_create(self, db_name="default", collection_name=None, partition_name=None):
        url = f'{self.endpoint}/v2/vectordb/partitions/create'
        if self.db_name is not None:
            db_name = self.db_name
        payload = {
            "dbName": db_name,
            "collectionName": collection_name,
            "partitionName": partition_name
        }
        response = self.post(url, headers=self.update_headers(), data=payload)
        res = response.json()
        return res

    def partition_drop(self, db_name="default", collection_name=None, partition_name=None):
        url = f'{self.endpoint}/v2/vectordb/partitions/drop'
        if self.db_name is not None:
            db_name = self.db_name
        payload = {
            "dbName": db_name,
            "collectionName": collection_name,
            "partitionName": partition_name
        }
        response = self.post(url, headers=self.update_headers(), data=payload)
        res = response.json()
        return res

    def partition_load(self, db_name="default", collection_name=None, partition_names=None):
        url = f'{self.endpoint}/v2/vectordb/partitions/load'
        if self.db_name is not None:
            db_name = self.db_name
        payload = {
            "dbName": db_name,
            "collectionName": collection_name,
            "partitionNames": partition_names
        }
        response = self.post(url, headers=self.update_headers(), data=payload)
        res = response.json()
        return res

    def partition_release(self, db_name="default", collection_name=None, partition_names=None):
        url = f'{self.endpoint}/v2/vectordb/partitions/release'
        if self.db_name is not None:
            db_name = self.db_name
        payload = {
            "dbName": db_name,
            "collectionName": collection_name,
            "partitionNames": partition_names
        }
        response = self.post(url, headers=self.update_headers(), data=payload)
        res = response.json()
        return res

    def partition_has(self, db_name="default", collection_name=None, partition_name=None):
        url = f'{self.endpoint}/v2/vectordb/partitions/has'
        if self.db_name is not None:
            db_name = self.db_name
        data = {
            "dbName": db_name,
            "collectionName": collection_name,
            "partitionName": partition_name
        }
        response = self.post(url, headers=self.update_headers(), data=data)
        res = response.json()
        return res

    def partition_stats(self, db_name="default", collection_name=None, partition_name=None):
        url = f'{self.endpoint}/v2/vectordb/partitions/get_stats'
        if self.db_name is not None:
            db_name = self.db_name
        data = {
            "dbName": db_name,
            "collectionName": collection_name,
            "partitionName": partition_name
        }
        response = self.post(url, headers=self.update_headers(), data=data)
        res = response.json()
        return res


class UserClient(Requests):

    def __init__(self, endpoint, token):
        super().__init__(url=endpoint, api_key=token)
        self.endpoint = endpoint
        self.api_key = token
        self.db_name = None
        self.headers = self.update_headers()

    def update_headers(self):
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
            'RequestId': str(uuid.uuid1())
        }
        return headers

    def user_list(self):
        url = f'{self.endpoint}/v2/vectordb/users/list'
        response = self.post(url, headers=self.update_headers())
        res = response.json()
        return res

    def user_create(self, payload):
        url = f'{self.endpoint}/v2/vectordb/users/create'
        response = self.post(url, headers=self.update_headers(), data=payload)
        res = response.json()
        return res

    def user_password_update(self, payload):
        url = f'{self.endpoint}/v2/vectordb/users/update_password'
        response = self.post(url, headers=self.update_headers(), data=payload)
        res = response.json()
        return res

    def user_describe(self, user_name):
        url = f'{self.endpoint}/v2/vectordb/users/describe'
        data = {
            "userName": user_name
        }
        response = self.post(url, headers=self.update_headers(), data=data)
        res = response.json()
        return res

    def user_drop(self, payload):
        url = f'{self.endpoint}/v2/vectordb/users/drop'
        response = self.post(url, headers=self.update_headers(), data=payload)
        res = response.json()
        return res

    def user_grant(self, payload):
        url = f'{self.endpoint}/v2/vectordb/users/grant_role'
        response = self.post(url, headers=self.update_headers(), data=payload)
        res = response.json()
        return res

    def user_revoke(self, payload):
        url = f'{self.endpoint}/v2/vectordb/users/revoke_role'
        response = self.post(url, headers=self.update_headers(), data=payload)
        res = response.json()
        return res


class RoleClient(Requests):

    def __init__(self, endpoint, token):
        super().__init__(url=endpoint, api_key=token)
        self.endpoint = endpoint
        self.api_key = token
        self.db_name = None
        self.headers = self.update_headers()

    def update_headers(self):
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
            'RequestId': str(uuid.uuid1())
        }
        return headers

    def role_list(self):
        url = f'{self.endpoint}/v2/vectordb/roles/list'
        response = self.post(url, headers=self.update_headers())
        res = response.json()
        return res

    def role_create(self, payload):
        url = f'{self.endpoint}/v2/vectordb/roles/create'
        response = self.post(url, headers=self.update_headers(), data=payload)
        res = response.json()
        return res

    def role_describe(self, role_name):
        url = f'{self.endpoint}/v2/vectordb/roles/describe'
        data = {
            "roleName": role_name
        }
        response = self.post(url, headers=self.update_headers(), data=data)
        res = response.json()
        return res

    def role_drop(self, payload):
        url = f'{self.endpoint}/v2/vectordb/roles/drop'
        response = self.post(url, headers=self.update_headers(), data=payload)
        res = response.json()
        return res

    def role_grant(self, payload):
        url = f'{self.endpoint}/v2/vectordb/roles/grant_privilege'
        response = self.post(url, headers=self.update_headers(), data=payload)
        res = response.json()
        return res

    def role_revoke(self, payload):
        url = f'{self.endpoint}/v2/vectordb/roles/revoke_privilege'
        response = self.post(url, headers=self.update_headers(), data=payload)
        res = response.json()
        return res


class IndexClient(Requests):

    def __init__(self, endpoint, token):
        super().__init__(url=endpoint, api_key=token)
        self.endpoint = endpoint
        self.api_key = token
        self.db_name = None
        self.headers = self.update_headers()

    def update_headers(self):
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
            'RequestId': str(uuid.uuid1())
        }
        return headers

    def index_create(self, payload, db_name="default"):
        url = f'{self.endpoint}/v2/vectordb/indexes/create'
        if self.db_name is not None:
            db_name = self.db_name
        payload["dbName"] = db_name
        response = self.post(url, headers=self.update_headers(), data=payload)
        res = response.json()
        return res

    def index_describe(self, db_name="default", collection_name=None, index_name=None):
        url = f'{self.endpoint}/v2/vectordb/indexes/describe'
        if self.db_name is not None:
            db_name = self.db_name
        data = {
            "dbName": db_name,
            "collectionName": collection_name,
            "indexName": index_name
        }
        response = self.post(url, headers=self.update_headers(), data=data)
        res = response.json()
        return res

    def index_list(self, collection_name=None, db_name="default"):
        url = f'{self.endpoint}/v2/vectordb/indexes/list'
        if self.db_name is not None:
            db_name = self.db_name
        data = {
            "dbName": db_name,
            "collectionName": collection_name
        }
        response = self.post(url, headers=self.update_headers(), data=data)
        res = response.json()
        return res

    def index_drop(self, payload, db_name="default"):
        url = f'{self.endpoint}/v2/vectordb/indexes/drop'
        if self.db_name is not None:
            db_name = self.db_name
        payload["dbName"] = db_name
        response = self.post(url, headers=self.update_headers(), data=payload)
        res = response.json()
        return res


class AliasClient(Requests):

    def __init__(self, endpoint, token):
        super().__init__(url=endpoint, api_key=token)
        self.endpoint = endpoint
        self.api_key = token
        self.db_name = None
        self.headers = self.update_headers()

    def update_headers(self):
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
            'RequestId': str(uuid.uuid1())
        }
        return headers

    def list_alias(self):
        url = f'{self.endpoint}/v2/vectordb/aliases/list'
        response = self.post(url, headers=self.update_headers())
        res = response.json()
        return res

    def describe_alias(self, alias_name):
        url = f'{self.endpoint}/v2/vectordb/aliases/describe'
        data = {
            "aliasName": alias_name
        }
        response = self.post(url, headers=self.update_headers(), data=data)
        res = response.json()
        return res

    def alter_alias(self, payload):
        url = f'{self.endpoint}/v2/vectordb/aliases/alter'
        response = self.post(url, headers=self.update_headers(), data=payload)
        res = response.json()
        return res

    def drop_alias(self, payload):
        url = f'{self.endpoint}/v2/vectordb/aliases/drop'
        response = self.post(url, headers=self.update_headers(), data=payload)
        res = response.json()
        return res

    def create_alias(self, payload):
        url = f'{self.endpoint}/v2/vectordb/aliases/create'
        response = self.post(url, headers=self.update_headers(), data=payload)
        res = response.json()
        return res


class ImportJobClient(Requests):

    def __init__(self, endpoint, token):
        super().__init__(url=endpoint, api_key=token)
        self.endpoint = endpoint
        self.api_key = token
        self.db_name = None
        self.headers = self.update_headers()

    def update_headers(self):
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
            'RequestId': str(uuid.uuid1())
        }
        return headers

    def list_import_jobs(self, payload, db_name="default"):
        payload["dbName"] = db_name
        data = payload
        url = f'{self.endpoint}/v2/vectordb/jobs/import/list'
        response = self.post(url, headers=self.update_headers(), data=data)
        res = response.json()
        return res

    def create_import_jobs(self, payload):
        url = f'{self.endpoint}/v2/vectordb/jobs/import/create'
        response = self.post(url, headers=self.update_headers(), data=payload)
        res = response.json()
        return res

    def get_import_job_progress(self, task_id):
        payload = {
            "taskID": task_id
        }
        url = f'{self.endpoint}/v2/vectordb/jobs/import/get_progress'
        response = self.post(url, headers=self.update_headers(), data=payload)
        res = response.json()
        return res


class StorageClient():

    def __init__(self, endpoint, access_key, secret_key, bucket_name):
        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket_name = bucket_name
        self.client = Minio(
            self.endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=False,
        )

    def upload_file(self, file_path, object_name):
        try:
            self.client.fput_object(self.bucket_name, object_name, file_path)
        except S3Error as exc:
            logger.error("fail to copy files to minio", exc)
