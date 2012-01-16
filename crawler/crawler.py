#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, progressbar, sys, tarfile

from ftplib import FTP
from xml.etree.ElementTree import ElementTree

FTP_SERVER = 'ftp.ncbi.nlm.nih.gov'
CACHE_DIRECTORY = 'PubMed'

def get_PubMed_XML_TAR_GZ():
    """
    This function downloads XML archive files from PubMed.
    """

    ftp = FTP(FTP_SERVER)
    ftp.login()

    ftp_filenames = (
        'pub/pmc/articles.A-B.tar.gz',
        'pub/pmc/articles.C-H.tar.gz',
        'pub/pmc/articles.I-N.tar.gz',
        'pub/pmc/articles.O-Z.tar.gz'
    )

    for remote_filename in ftp_filenames:
        local_filename = os.path.join(CACHE_DIRECTORY,
            os.path.split(remote_filename)[-1])

        ftp.sendcmd('TYPE i')  # switch to binary mode,
        remote_filesize = ftp.size(remote_filename)
        try:
            local_filesize = os.stat(local_filename).st_size
        except OSError:  # File does not exist
            local_filesize = 0

        if remote_filesize == local_filesize:
            sys.stderr.write("%s is up to date, skipping.\n" % local_filename)
        else:
            sys.stderr.write("Downloading %s from %s, saving as %s …\n" % \
                (remote_filename, FTP_SERVER, local_filename))

            with open(local_filename, 'wb') as f:
                p = progressbar.ProgressBar(maxval=remote_filesize)

                def callback(chunk):
                    f.write(chunk)
                    p.update(p.currval + len(chunk))

                ftp.retrbinary("RETR %s" % remote_filename, callback)

    ftp.quit()

get_PubMed_XML_TAR_GZ()

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
