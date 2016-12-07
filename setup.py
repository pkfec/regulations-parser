from setuptools import setup, find_packages

setup(
    name="regparser",
    version="4.1.0",
    packages=find_packages(),
    classifiers=[
        'License :: Public Domain',
        'License :: CC0 1.0 Universal (CC0 1.0) Public Domain Dedication'
    ],
    install_requires=[
        "attrs",
        "cached-property",
        "click",
        "coloredLogs",
        "Django==1.9.*",
        "dj-database-url",
        "django-click",
        "django_rq",
        "djangorestframework",
        "GitPython",
        "inflection",
        "ipdb",
        "json-delta",
        "lxml",
        "networkx",
        "pyparsing",
        "python-constraint",
        "requests",
        "requests-cache",
        "roman",
        "six",
        "stevedore"
    ],
    entry_points={
        "console_scripts": "eregs=eregs:main",
        "eregs_ns.parser.layer.cfr": [
            "meta = regparser.layer.meta:Meta",
            ("internal-citations = regparser.layer.internal_citations:"
             "InternalCitationParser"),
            "toc = regparser.layer.table_of_contents:TableOfContentsLayer",
            "terms = regparser.layer.terms:Terms",
            ("paragraph-markers = regparser.layer.paragraph_markers:"
             "ParagraphMarkers"),
            "keyterms = regparser.layer.key_terms:KeyTerms",
            ("external-citations = regparser.layer.external_citations:"
             "ExternalCitationParser"),
            "formatting = regparser.layer.formatting:Formatting",
            "graphics = regparser.layer.graphics:Graphics",
        ],
        "eregs_ns.parser.layer.preamble": [
            "keyterms = regparser.layer.preamble.key_terms:KeyTerms",
            ("internal-citations = regparser.layer.preamble."
             "internal_citations:InternalCitations"),
            ("paragraph-markers = regparser.layer.preamble.paragraph_markers:"
             "ParagraphMarkers"),
            ("external-citations = regparser.layer.external_citations:"
             "ExternalCitationParser"),
            "formatting = regparser.layer.formatting:Formatting",
            "graphics = regparser.layer.graphics:Graphics",
        ],
        "eregs_ns.parser.preprocessors": [
            ("move-last-amdpar = regparser.tree.xml_parser.preprocessors:"
             "MoveLastAMDPar"),
            ("supplement-amd-par = regparser.tree.xml_parser.preprocessors:"
             "SupplementAMDPar"),
            ("parenthesis-cleanup = regparser.tree.xml_parser.preprocessors:"
             "ParenthesesCleanup"),
            ("move-adjoining-chars = regparser.tree.xml_parser.preprocessors:"
             "MoveAdjoiningChars"),
            ("approvals-fp = regparser.tree.xml_parser.preprocessors:"
             "ApprovalsFP"),
            ("extract-tags = regparser.tree.xml_parser.preprocessors:"
             "ExtractTags"),
            "footnotes = regparser.tree.xml_parser.preprocessors:Footnotes",
            ("parse-amdpars = regparser.tree.xml_parser.preprocessors:"
             "ParseAMDPARs"),
            "atf-i-50032 = regparser.tree.xml_parser.preprocessors:AtfI50032",
            "atf-i-50031 = regparser.tree.xml_parser.preprocessors:AtfI50031",
            ("atf-import-categories = regparser.tree.xml_parser.preprocessors:"
             "ImportCategories"),
        ]
    }
)
