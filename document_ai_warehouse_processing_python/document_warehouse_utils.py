import json
from typing import Optional, List

from google.cloud import contentwarehouse_v1
import google.cloud.documentai_v1 as docai
import document_ai_utils


class document_warehouse_utils:

    def __init__(self, project_number: str, api_location: str,
                 document_service_client: contentwarehouse_v1.DocumentServiceClient = None):
        self.project_number = project_number
        self.api_location = api_location

        self.document_service_client = None
        self.document_link_service_client = None
        self.document_schema_service_client = None

    def get_document_link_service_client(self) -> contentwarehouse_v1.DocumentLinkServiceClient:
        if not self.document_link_service_client:
            self.document_link_service_client = contentwarehouse_v1.DocumentLinkServiceClient()
        return self.document_link_service_client

    def get_document_service_client(self) -> contentwarehouse_v1.DocumentServiceClient:
        if not self.document_service_client:
            self.document_service_client = contentwarehouse_v1.DocumentServiceClient()
        return self.document_service_client

    def get_document_schema_service_client(self) -> contentwarehouse_v1.DocumentSchemaServiceClient:
        if not self.document_schema_service_client:
            self.document_schema_service_client = contentwarehouse_v1.DocumentSchemaServiceClient()
        return self.document_schema_service_client

    def fetch_acl(self, document_id: str,
                  caller_user_id: str) -> contentwarehouse_v1.FetchAclResponse:
        # Create a client
        client = self.get_document_service_client()
        parent = client.common_location_path(self.project_number, self.api_location)

        request = contentwarehouse_v1.FetchAclRequest()

        # Initialize request argument(s)
        request.resource = f"{parent}/documents/{document_id}"
        request.request_metadata.user_info.id = caller_user_id

        # Make the request
        response = client.fetch_acl(request=request)

        # Handle the response
        return response

    def copy_document_acl_to_document(self, target_document_id: str, source_document_id: str,
                caller_user_id: str):
        fetch_acl_response = self.fetch_acl(source_document_id, caller_user_id=caller_user_id)

        document_policy = fetch_acl_response.policy

        self.set_acl(document_id=target_document_id, policy=document_policy,caller_user_id=caller_user_id)

        print(f"ACL copied from source document:{source_document_id} to target document:{target_document_id}")

    def set_acl(self, document_id: str, policy: str,
                caller_user_id: str) -> contentwarehouse_v1.SetAclResponse:

        if len(document_id) == 0 or policy:
            return False, 'document_id or policy is empty'

        # Create a client
        client = self.get_document_service_client()
        parent = client.common_location_path(self.project_number, self.api_location)

        request = contentwarehouse_v1.SetAclRequest()

        # Initialize request argument(s)

        request.resource = f"{parent}/documents/{document_id}"
        request.policy = policy
        request.request_metadata.user_info.id = caller_user_id

        # Make the request
        response = client.set_acl(request=request)

        # Handle the response
        return response

    # Document methods

    def search_documents(self, query: str, caller_user_id: str) -> contentwarehouse_v1.SearchDocumentsResponse:

        # Create a client
        client = self.get_document_service_client()
        parent = client.common_location_path(self.project_number, self.api_location)

        # Initialize request argument(s)
        request = contentwarehouse_v1.SearchDocumentsRequest()
        request.parent = parent
        request.document_query.query = query

        request.request_metadata.user_info.id = caller_user_id

        # Make the request
        response = client.search_documents(request=request)

        # Handle the response
        return response

    def delete_document(self, document_id: str, caller_user_id: str) -> None:
        # Create a client
        client = self.get_document_service_client()
        parent = client.common_location_path(self.project_number, self.api_location)

        # Initialize request argument(s)
        request = contentwarehouse_v1.DeleteDocumentRequest()
        request.name = f"{parent}/documents/{document_id}"
        request.request_metadata.user_info.id = caller_user_id

        # Make the request
        client.delete_document(request=request)

    def get_document(self, document_id: str, caller_user_id: str) -> contentwarehouse_v1.Document:
        # Create a client
        client = self.get_document_service_client()
        parent = client.common_location_path(self.project_number, self.api_location)

        # Initialize request argument(s)
        request = contentwarehouse_v1.GetDocumentRequest()
        request.name = f"{parent}/documents/{document_id}"
        request.request_metadata.user_info.id = caller_user_id

        # Make the request
        response = client.get_document(request=request)

        # Handle the response
        return response

    def link_document_to_folder(self, document_id: str, folder_document_id: str, caller_user_id: str):
        if len(folder_document_id) == 0:
            return False, ''

        try:
            # Create a client
            client = self.get_document_link_service_client()
            parent = client.common_location_path(self.project_number, self.api_location)

            request = contentwarehouse_v1.CreateDocumentLinkRequest()

            # Initialize request argument(s)
            request.parent = f"{parent}/documents/{folder_document_id}"
            request.document_link.target_document_reference.document_name = f"{parent}/documents/{document_id}"
            request.document_link.source_document_reference.document_name = f"{parent}/documents/{folder_document_id}"
            request.request_metadata.user_info.id = caller_user_id

            # Make the request
            response = client.create_document_link(request=request)

            # Handle the response
            return response

        except Exception as e:
            error_msg = str(e)[:100]
            return False, error_msg


    @staticmethod
    def set_raw_document_file_type_from_mimetype(document: contentwarehouse_v1.Document, mime_type):
        mime_to_dw_mime_enum = {
            "application/pdf": document.raw_document_file_type.RAW_DOCUMENT_FILE_TYPE_PDF,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": document.raw_document_file_type.RAW_DOCUMENT_FILE_TYPE_DOCX,
            "text/plain": document.raw_document_file_type.RAW_DOCUMENT_FILE_TYPE_TEXT,
            "application/vnd.openxmlformats-officedocument.presentationml.presentation": document.raw_document_file_type.RAW_DOCUMENT_FILE_TYPE_PPTX,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":  document.raw_document_file_type.RAW_DOCUMENT_FILE_TYPE_XLSX,
        }
        if mime_type.lower() in mime_to_dw_mime_enum:
            document.raw_document_file_type =  mime_to_dw_mime_enum[mime_type.lower()]
        else:
            document.raw_document_file_type = document.raw_document_file_type.RAW_DOCUMENT_FILE_TYPE_UNSPECIFIED

    def apped_docai_entities_to_doc_properties(self,cloud_ai_document: docai.Document, document: contentwarehouse_v1.Document, docai_property_name: str):
        # Append doc ai document entities if exists
        if cloud_ai_document:
            entities = document_ai_utils.get_entities(cloud_ai_document)
            if len(entities) > 0:
                map_property = contentwarehouse_v1.MapProperty()
                for key in entities:
                    value = contentwarehouse_v1.Value()
                    value.string_value = entities[key]
                    map_property.fields[key] = value

                one_property = contentwarehouse_v1.Property()
                one_property.map_property = map_property
                one_property.name = docai_property_name
                document.properties.append(one_property)

    def create_document(
            self,
            display_name: str,
            document_schema_id: str,
            caller_user_id: str,
            metadata_properties: List[contentwarehouse_v1.Property] = [],
            reference_id: str = "",
            docai_property_name: str = "document_ai_entities",
            raw_document_path: str = None,
            mime_type: str = None,
            raw_inline_bytes: str = None,
            document_text: str = None,
            apped_docai_entities_to_doc_properties: bool = False,
            cloud_ai_document: Optional[docai.Document] = None) -> contentwarehouse_v1.Document:

        # Create a client
        client = self.get_document_service_client()
        parent = client.common_location_path(self.project_number, self.api_location)

        # Initialize request argument(s)
        document = contentwarehouse_v1.Document()
        document.raw_document_path = raw_document_path
        document.display_name = display_name
        document.title = display_name
        document.reference_id = reference_id
        document.inline_raw_document = raw_inline_bytes
        document.text_extraction_disabled = False
        self.set_raw_document_file_type_from_mimetype(document = document, mime_type=mime_type)

        # Add properties from metadata

        if len(metadata_properties) > 0:
            document.properties.extend(metadata_properties)

        if cloud_ai_document:
            document.cloud_ai_document = cloud_ai_document._pb
            if apped_docai_entities_to_doc_properties:
                self.apped_docai_entities_to_doc_properties(cloud_ai_document = cloud_ai_document, document = document, docai_property_name= docai_property_name)
        elif document_text:
            document.plain_text = document_text

        document.document_schema_name = f"{parent}/documentSchemas/{document_schema_id}"

        request = contentwarehouse_v1.CreateDocumentRequest(
            parent=parent,
            document=document,
        )

        request.request_metadata.user_info.id = caller_user_id

        # Make the request
        response = client.create_document(request=request)

        # Handle the response
        return response


    # Schema

    @staticmethod
    def create_document_schema_property_definition(property_definition: dict) -> contentwarehouse_v1.PropertyDefinition():
        prop = contentwarehouse_v1.PropertyDefinition()
        prop.name = property_definition["name"]

        prop.display_name = property_definition["display_name"]
        prop.is_filterable = property_definition["is_filterable"]
        prop.is_repeatable = property_definition["is_repeatable"]
        prop.is_searchable = property_definition["is_searchable"]
        prop.is_metadata = property_definition["is_metadata"]
        prop.is_required = property_definition["is_required"]

        if "integer_type_options" in property_definition:
            prop.integer_type_options =  property_definition["integer_type_options"]
        elif "text_type_options" in property_definition:
            prop.text_type_options =  property_definition["text_type_options"]
        elif "float_type_options" in property_definition:
            prop.float_type_options = property_definition["float_type_options"]
        elif "timestamp_type_options" in property_definition:
            prop.timestamp_type_options = property_definition["timestamp_type_options"]
        elif "property_type_options" in property_definition:
            prop.property_type_options = property_definition["property_type_options"]
        elif "date_time_type_options" in property_definition:
            prop.date_time_type_options = property_definition["date_time_type_options"]
        elif "enum_type_options" in property_definition:
            prop.enum_type_options = property_definition["enum_type_options"]
        elif "map_type_options" in property_definition:
            prop.map_type_options = property_definition["map_type_options"]

        return prop

    def create_document_schema(self, schema) -> contentwarehouse_v1.DocumentSchema:

        schema_json = json.loads(schema)

        client = self.get_document_schema_service_client()
        parent = client.common_location_path(self.project_number, self.api_location)

        # Initialize request argument(s)
        request = contentwarehouse_v1.CreateDocumentSchemaRequest()

        request.parent = parent

        # define schema
        request.document_schema = contentwarehouse_v1.DocumentSchema()
        request.document_schema.display_name = schema_json["display_name"]
        request.document_schema.document_is_folder = schema_json["document_is_folder"]
        request.document_schema.description = schema_json["description"]

        for property_definition in schema_json["property_definitions"]:
            request.document_schema.property_definitions.append(self.create_document_schema_property_definition(property_definition))

        print(request)
        print(request.document_schema)

        #Make the request
        response = client.create_document_schema(request=request)

        # Handle the response
        return response

    def get_document_schema(self,schema_id: str):
        client = self.get_document_schema_service_client()
        parent = client.common_location_path(self.project_number, self.api_location)

        # Initialize request argument(s)
        request = contentwarehouse_v1.GetDocumentSchemaRequest()

        request.name = f"{parent}/documentSchemas/{schema_id}"

        # Make the request
        response = client.get_document_schema(request=request)

        # Handle the response
        return response

    def delete_document_schema(self,schema_id: str):

        client = self.get_document_schema_service_client()
        parent = client.common_location_path(self.project_number, self.api_location)

        # Initialize request argument(s)
        request = contentwarehouse_v1.DeleteDocumentSchemaRequest()

        request.name = f"{parent}/documentSchemas/{schema_id}"

        # Make the request
        response = client.delete_document_schema(request=request)

        # Handle the response
        return response

    def update_document_schema(self, schema_id: str, schema: str):
        schema_json = json.loads(schema)

        client = self.get_document_schema_service_client()
        parent = client.common_location_path(self.project_number, self.api_location)

        # Initialize request argument(s)
        request = contentwarehouse_v1.UpdateDocumentSchemaRequest()

        request.name = f"{parent}/documentSchemas/{schema_id}"

        # define schema
        request.document_schema = contentwarehouse_v1.DocumentSchema()
        request.document_schema.display_name = schema_json["display_name"]
        request.document_schema.document_is_folder = schema_json["document_is_folder"]
        request.document_schema.description = schema_json["description"]

        for property_definition in schema_json["property_definitions"]:
            request.document_schema.property_definitions.append(
                self.create_document_schema_property_definition(property_definition))

        print(request)
        print(request.document_schema)

        # Make the request
        response = client.update_document_schema(request=request)

        # Handle the response
        return response
