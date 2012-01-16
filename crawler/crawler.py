#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, progressbar, sys, tarfile

from ftplib import FTP
from xml.etree.ElementTree import ElementTree

CACHE_DIRECTORY = 'PubMed'

FTP_SERVER = 'ftp.ncbi.nlm.nih.gov'
FTP_FILENAMES = [
    'pub/pmc/articles.A-B.tar.gz',
    'pub/pmc/articles.C-H.tar.gz',
    'pub/pmc/articles.I-N.tar.gz',
    'pub/pmc/articles.O-Z.tar.gz'
]

LOCAL_FILENAMES = [
    os.path.join(CACHE_DIRECTORY, os.path.split(remote_filename)[-1])
    for remote_filename in FTP_FILENAMES
]

def get_PubMed_XML_TAR_GZ():
    """
    This function downloads XML archive files from PubMed.
    """

    ftp = FTP(FTP_SERVER)
    ftp.login()

    for i,remote_filename in enumerate(FTP_FILENAMES):
        local_filename = LOCAL_FILENAMES[i]

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


def PubMed_absolute_URL(PMCID, href):
    """
    This function creates absolute URIs for supplementary materials,
    using a PubMed Central ID and a relative URI.
    """
    PREFIX = 'http://www.ncbi.nlm.nih.gov/pmc/articles/PMC'
    SUFFIX = '/bin/'

    return str(PREFIX + PMCID + SUFFIX + href)


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
                for xref in tree.iter('xref'):
                    try:
                        if xref.attrib['ref-type'] == 'supplementary-material':
                            rid = xref.attrib['rid']
                            for sup in tree.iter('supplementary-material'):
                                if sup.attrib['id'] == rid:
                                    media = ElementTree(sup).find('media')
                                    if media.attrib['mimetype']:  # in ('audio', 'video'):
                                        href = media.attrib['{http://www.w3.org/1999/xlink}href']
                                        for aid in tree.iter('article-id'):
                                            if aid.attrib['pub-id-type'] == 'pmc':
                                                PMCID = aid.text
                                        sys.stderr.write(
                                            PubMed_absolute_URL(PMCID, href) + '\n'
                                        )
                                        sys.stderr.flush()
                    except KeyError:
                        pass
                    except AttributeError:
                        pass


if __name__ == '__main__':
    get_PubMed_XML_TAR_GZ()

    for f in LOCAL_FILENAMES:
        find_PubMed_articles_with_supplementary_materials(f)
