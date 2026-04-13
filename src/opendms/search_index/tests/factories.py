import factory

from ..index import Document, Zaak


class IndexZaakFactory(factory.Factory):
    uuid = factory.Faker("uuid4", cast_to=str)
    url = factory.Faker("url")
    identificatie = factory.Faker("uuid4", cast_to=str)
    bronorganisatie = factory.Faker("company")
    verantwoordelijkeOrganisatie = factory.Faker("company")
    omschrijving = factory.Faker("sentence", nb_words=6)
    toelichting = factory.Faker("paragraph")
    status = factory.Faker("word")
    registratiedatum = factory.Faker("past_date")
    startdatum = factory.Faker("past_date")
    zaaktype = factory.Faker("word")

    service_slug = "zaken-api"
    ztc_service_slug = "catalogi-api"
    group_slug = "group-1"

    class Meta:
        model = Zaak


class NestedzaakFactory(factory.Factory):
    uuid = factory.Faker("uuid4", cast_to=str)
    url = factory.Faker("url")
    identificatie = factory.Faker("uuid4", cast_to=str)
    bronorganisatie = factory.Faker("company")
    verantwoordelijkeOrganisatie = factory.Faker("company")
    omschrijving = factory.Faker("sentence", nb_words=6)
    toelichting = factory.Faker("paragraph")
    status = factory.Faker("word")
    registratiedatum = factory.Faker("past_date")
    startdatum = factory.Faker("past_date")
    zaaktype = factory.Faker("word")
    object_type = factory.Faker("word")

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
    bestandsomvang = 1000000
    link = factory.Faker("url")
    creatiedatum = factory.Faker("past_date")
    begin_registratie = factory.Faker("past_datetime")

    zaak_referenties = factory.List([factory.SubFactory(NestedzaakFactory)])

    class Meta:
        model = Document
