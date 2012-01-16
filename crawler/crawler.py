#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys, tarfile

from ftplib import FTP
from xml.etree.ElementTree import ElementTree

DIRECTORY = 'PubMed'

def get_PubMed_XML_TAR_GZ():
    """
    This function downloads XML archive files from PubMed.
    """
    SERVER = 'ftp.ncbi.nlm.nih.gov'

    ftp = FTP(SERVER)
    ftp.login()

    filenames = {
        'pub/pmc/articles.A-B.tar.gz': 'articles.A-B.tar.gz',
        'pub/pmc/articles.C-H.tar.gz': 'articles.C-H.tar.gz',
        'pub/pmc/articles.I-N.tar.gz': 'articles.I-N.tar.gz',
        'pub/pmc/articles.O-Z.tar.gz': 'articles.O-Z.tar.gz'
    }

    for remote_name, local_name in filenames.iteritems():
        sys.stderr.write("Downloading %s from %s, saving as %s …" % (
            remote_name, SERVER, local_name)
        )
        ftp.retrbinary(
            "RETR %s" % remote_name,
            open(
                os.path.join(DIRECTORY, local_name), 'wb'
            ).write
        )
        sys.stderr.write('done.\n')

    ftp.quit()


def find_PubMed_articles_with_supplementary_materials(filename):
    """
    This function finds articles having supplementary materials.
    """
    with tarfile.open(filename) as archive:
        for item in archive:
            if os.path.splitext(item.name)[1] == '.nxml':
                content = archive.extractfile(item)
                tree = ElementTree()
                tree.parse(content)
                for element in tree.iter('xref'):
                    try:
                        if element.attrib['ref-type'] == 'supplementary-material':
                            print element.attrib, element.text
                    except KeyError:
                        pass
    # TODO: return a list of identifiers

find_PubMed_articles_with_supplementary_materials('PubMed/articles.A-B.tar.gz')
