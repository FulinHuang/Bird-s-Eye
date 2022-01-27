import boto3
from boto3.dynamodb.conditions import Key, Attr
import json
from decimal import Decimal


class AWSManager:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        self.s3_client = boto3.client('s3', region_name='us-east-1')

    def create_user_table(self):
        table = self.dynamodb.create_table(
            TableName='Users',
            KeySchema=[
                {
                    'AttributeName': 'username',
                    'KeyType': 'HASH'  # HASH for partition key, RANGE for sort key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'username',
                    'AttributeType': 'S' # S for String, N for Number
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        return table

    def create_photo_table(self):
        table = self.dynamodb.create_table(
            TableName='Photos',
            KeySchema=[
                {
                    'AttributeName': 'photourl',
                    'KeyType': 'HASH'  # HASH for partition key, RANGE for sort key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'photourl',
                    'AttributeType': 'S' # S for String, N for Number
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        return table

    def create_s3_bucket(self):
        # Create bucket
        self.s3_client.create_bucket(Bucket='ece1779a3allenyw123')
        return

    def add_table_item(self, table_name, item):
        table = self.dynamodb.Table(table_name)
        response = table.put_item(Item = item)
        return response

    def update_table_item(self, table_name, key, column, new_value):
        '''
        :param table_name: the name of the table, Users or Photos
        :param key: the partition key:{"username": ""} or {"photourl": ""}
        :param column: the column that you wanna update
        :param new_value: the new value of that column, has to be string
        :return: updated values
        '''
        table = self.dynamodb.Table(table_name)
        response = table.update_item(
            Key=key,
            UpdateExpression="set "+column+"=:r",
            ExpressionAttributeValues={
                ':r': new_value
            },
            ReturnValues="UPDATED_NEW"
        )
        return response

    def increase_table_column(self, table_name, key, column, increase):
        '''
        :param table_name: the name of the table, Users or Photos
        :param key: the partition key:{"username": ""} or {"photourl": ""}
        :param column: the column that you wanna increase
        :param increase: the amount of increase
        :return: updated values
        '''
        table = self.dynamodb.Table(table_name)
        response = table.update_item(Key = key,
                                     UpdateExpression = "set "+column+" = "+column+" + :val",
                                     ExpressionAttributeValues={
                                         ':val': Decimal(str(increase))
                                     },
                                     ReturnValues = "UPDATED_NEW")
        return response

    def delete_table_item(self, table_name, item):
        '''
        :param table_name:
        :param item: should be {"username": username} or {"photourl: photourl}
        :return:
        '''
        table = self.dynamodb.Table(table_name)
        response = table.delete_item(Key = item)
        return response

    def query_table_item(self, table_name, key, value):
        # query the table must use the partition key.
        table = self.dynamodb.Table(table_name)
        response = table.query(
            KeyConditionExpression=Key(key).eq(value)
        )
        return response['Items']

    def scan_table_item(self, table_name, key, value):
        table = self.dynamodb.Table(table_name)
        response = table.scan(
            FilterExpression = Attr(key).eq(value)
        )
        return response['Items']

    def scan_table_contain_item(self, table_name, key, value):
        table = self.dynamodb.Table(table_name)
        response = table.scan(
            FilterExpression = Attr(key).contains(value)
        )
        return response['Items']

    def scan_table_condition_item(self, table_name, key, value):
        table = self.dynamodb.Table(table_name)
        response = table.scan(
            FilterExpression = Attr(key).gt(value)
        )
        return response['Items']

    def append_table_item(self, table_name, key, column, value):
        table = self.dynamodb.Table(table_name)
        response = table.update_item(
            Key=key,
            UpdateExpression="SET "+column+" = list_append("+column+", :i)",
            ExpressionAttributeValues={
                ':i': value
            },
            ReturnValues="UPDATED_NEW"
        )
        return response

if __name__ == '__main__':
    # initialization
    manager = AWSManager()

    # # create user table
    #user_table = manager.create_user_table()
    # # create photo table
    #photo_table = manager.create_photo_table()
    # create s3 bucket
    # manager.create_s3_bucket()
    # upload the default avatar to S3
    # manager.s3_client.upload_file("static/avatar/dft.png", 'ece1779a3allenyw123', 'avatar/dft.png',ExtraArgs={'ACL':'public-read'})

    # 给database里的user加上热度, 并更新一下热度。
    # all_users = manager.dynamodb.Table('Users').scan()['Items']
    # for user in all_users:
    #      photos = manager.scan_table_item("Photos", "username", user["username"])
    #      sum_popularity = sum([photo["click_rate"] for photo in photos])
    #      manager.update_table_item("Users", {"username": user["username"]}, "popularity", sum_popularity)

    # 把databases里photo的comments，原来是"", 现在变成[]。
    all_photos = manager.dynamodb.Table('Photos').scan()['Items']
    for photo in all_photos:
        manager.update_table_item("Photos", {"photourl": photo["photourl"]}, "comments", [])

