import factory
from zgw_consumers.constants import APITypes, AuthTypes
from zgw_consumers.test.factories import ServiceFactory as _ServiceFactory


class NestedPublisherFactory(factory.Factory):
    uuid = factory.Faker("uuid4", cast_to=str)
    naam = factory.Faker("company")

    class Meta:
        model = dict


class IndexDocumentFactory(factory.Factory):
    uuid = factory.Faker("uuid4", cast_to=str)
    url = factory.Faker("url")
    identificatie = factory.Faker("uuid4", cast_to=str)
    bronorganisatie = factory.Faker("company")
    titel = factory.Faker("sentence", nb_words=6)
    beschrijving = factory.Faker("paragraph")
    auteur = factory.Faker("name")
    taal = factory.Faker("language_code")
    vertrouwelijkheidaanduiding = factory.Faker("word")
    status = factory.Faker("word")
    formaat = factory.Faker("file_extension")
    bestandsnaam = factory.Faker("file_name")
    informatieobjecttype = factory.Faker("word")
    verschijningsvorm = factory.Faker("word")
    inhoud = factory.Faker("paragraph")
    link = factory.Faker("url")
    creatiedatum = factory.Faker("past_date")
    ontvangstdatum = factory.Faker("past_date")
    verzenddatum = factory.Faker("past_date")
    begin_registratie = factory.Faker("past_datetime")

    class Meta:
        model = dict


class ServiceFactory(_ServiceFactory):
    class Params:
        for_download_url_mock_service = factory.Trait(
            label="download-url-mock",
            api_root="http://localhost/",
            api_type=APITypes.orc,
            auth_type=AuthTypes.api_key,
            header_key="Authorization",
            header_value="Token insecure",
        )
