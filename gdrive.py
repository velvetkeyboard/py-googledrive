import re
import logging
import pickle
import os.path
from googleapiclient.http import MediaFileUpload
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pysnooper


# If modifying these scopes, delete the file token.pickle.
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    ]


class MimeType:
    FOLDER = 'application/vnd.google-apps.folder'
    FILE = 'application/vnd.google-apps.file'
    UNKNOWN = 'application/vnd.google-apps.unknown'


class GoogleDrive(object):

    def __init__(self, creds=None):
        self.creds = creds or self.get_creds()
        self.svc = build('drive', 'v3', credentials=self.creds)

    def get_creds(self):
        # The file token.pickle stores the user's access and refresh tokens,
        # and is created automatically when the authorization flow completes
        # for the first time.
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                self.creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json',
                    SCOPES,
                    )
                self.creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(self.creds, token)
        return self.creds

    def query(self, params, fields):
        return self.svc.files().list(
            q=params,
            fields=fields,
            ).execute()

    def get_file_id(self, name, mime=None, trashed=None):
        trashed = 'true' if trashed else 'false'
        q = f"name = '{name}' and trashed = {trashed}"
        if mime:
            q += f" and mimeType = '{mime}'"
        fields = 'files(id, mimeType)'
        files = self.query(q, fields).get('files', [])
        if files:
            return files[0].get('id')

    def get_file(self, name, fields=None, filters=None, trashed=None):
        q = f"name = '{name}'"
        fields = 'files(id, name, mimeType, parents)'
        files = self.query(
            q,
            fields=fields,
            ).get('files', [])
        if len(files) == 1:
            return files[0]
        elif len(files) > 1:
            Exception(f'More than one file matches name "{name}"')

    def create_file(self, local_file_path, name, parent=None):
        if parent:
            parents = [self.get_folder_id(parent)]
        else:
            parents = []
        body = {
                'name': f'{name}',
                'parents': parents,
                }
        media_body = MediaFileUpload(
                local_file_path,
                )
        _file = self.svc.files().create(
            body=body,
            media_body=media_body,
            fields='id'
            ).execute()
        return _file

    def delete_file(self, name):
        file_id = self.get_file_id(name)
        ret = self.svc.files().delete(
                fileId=file_id,
                ).execute()

    def get_folder_id(name, trashed=False):
        return self.get_file_id(name, MimeType.FOLDER)

    def get_folder(self, name, fields=None, trashed=False):
        trashed = str(trashed).lower()
        if not fields:
            fields = 'files(id, name, parents)'
        q = f"name = '{name}'" \
            f"and mimeType = '{MimeType.FOLDER}'" \
            f"and trashed = {trashed}"
        files = self.query(q, fields).get('files', [])
        if len(files) > 1:
            raise Exception('Got more than 1: {}'.format(
                ', '.join([f"{fl['name']} {fl['id']}" for fl in files])
                ))
        elif len(files) == 1:
            return files[0]

    def get_folders(self, parents=None, fields=None, trashed=False):
        trashed = str(trashed).lower()
        if not fields:
            fields = 'files(id, name, parents)'
        q = f"mimeType = '{MimeType.FOLDER}' " \
            " and " \
            f"trashed = {trashed}"
        if parents:
            parents_ids = []
            for name in parents:
                parents_ids.append(self.get_folder(name).get('id'))
            parents_ids = ', '.join(parents_ids)
            q += f" and '{parents_ids}' in parents"
        return self.query(q, fields).get('files', [])

    def create_folder(self, name, parent=None, allow_duplicated=True):
        if not allow_duplicated:
            if self.get_file_id(name, MimeType.FOLDER):
                return
        body = {
            'name': f'{name}',
            'mimeType': MimeType.FOLDER,
            }
        if parent:
            parent = self.get_folder(parent).get('id')
            body['parents'] = [parent]
        ret = self.svc.files().create(
                body=body,
                fields='id',
                ).execute()
        return ret

    def delete_folder(self, name):
        folder_id = self.get_file_id(name, MimeType.FOLDER)
        ret = self.svc.files().delete(
                fileId=folder_id,
                ).execute()

class File(GoogleDrive):
    def __init__(self, name, uid=None, local_file_path=None):
        self.name = name
        self.uid = uid
        self.local_file_path = local_file_path
        super(File, self).__init__()

    def get_media_body(self, local_file_path=None):
        filename = local_file_path or self.local_file_path
        if not filename:
            raise Exception('local path for file was not defined')
        return MediaFileUpload(
            filename,
            )

class Folder(GoogleDrive):
    def __init__(self, name, uid=None):
        self.name = name
        self.uid = uid
        super(Folder, self).__init__()

    def get_uid(self):
        if self.uid:
            return self.uid
        self.uid = self.get_folder_id(self.name)
        return self.uid

    def create(self, parents=None, allow_duplicated=True):
        if not allow_duplicated:
            if self.get_file_id(name, MimeType.FOLDER):
                return
        body = {
            'name': f'{self.name}',
            'mimeType': MimeType.FOLDER,
            }
        if parents:
            body['parents'] = []
            for p in parents:
                body['parents'].append(
                    p.get_uid()
                    )
        resp = self.svc.files().create(
                body=body,
                fields='id,mimeType',
                ).execute()
        self.uid = resp.get('id')
        return resp

    def delete(self):
        self.svc.files().delete(
            fileId=self.get_uid(),
            ).execute()
        self.uid = None

    def upload_file(self, file_obj):
        parents = [self.get_uid()]
        body = {
            'name': f'{file_obj.name}',
            'parents': parents,
            }
        media_body = file_obj.get_media_body()
        resp = self.svc.files().create(
            body=body,
            media_body=media_body,
            fields='id'
            ).execute()
        file_obj.uid = resp.get('id')
        return file_obj

