#!/usr/bin/env python
# -*- coding: utf-8 -*-

#    Open Access Media Importer
#    crawler.py - download supplementary materials of open access articles
#
#    Copyright (C) 2012  Nils Dagson Moskopp <nils@dieweltistgarnichtso.net>
#    Copyright (C) 2012  Raphael Wimmer <raphael.wimmer@ifi.lmu.de>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os, progressbar, sys, tarfile

from ftplib import FTP
from xml.etree.ElementTree import ElementTree


CACHE_DIRECTORY = 'cache'
CACHE_PUBMED = 'PubMed'

FTP_SERVER = 'ftp.ncbi.nlm.nih.gov'
FTP_FILENAMES = [
    'pub/pmc/articles.A-B.tar.gz',
    'pub/pmc/articles.C-H.tar.gz',
    'pub/pmc/articles.I-N.tar.gz',
    'pub/pmc/articles.O-Z.tar.gz'
]

def get_PubMed_XML_TAR_GZ():
    """
    This function downloads XML archive files from PubMed.
    """
    cache_dir = os.path.join(CACHE_DIRECTORY, CACHE_PUBMED)
    try:
        os.makedirs(cache_dir)
    except OSError:
        try:
            os.stat(cache_dir)
        except OSError:
            sys.stderr.write("Cannot create cache directory. Aborting.\n")
            sys.exit(1)
        else:
            sys.stderr.write("Cache directory already exists. Using it.\n")

    local_files = ftp_download_files(FTP_SERVER, FTP_FILENAMES, cache_dir)
    return local_files

def ftp_download_files(server, filenames, local_dir, skip_same_sized=True):
    """
    Download a list of files from a ftp server into a local directory. 
    Optionally skip files that have the same size locally and on the server.
    """

    downloaded_filenames = []
    ftp = FTP(server)
    ftp.login()

    for i,remote_filename in enumerate(filenames):
        local_filename =  os.path.join(local_dir, os.path.split(remote_filename)[-1])
        downloaded_filenames.append(local_filename)

        ftp.sendcmd('TYPE i')  # switch to binary mode,
        remote_filesize = ftp.size(remote_filename)
        try:
            local_filesize = os.stat(local_filename).st_size
        except OSError:  # File does not exist
            local_filesize = 0

        if remote_filesize == local_filesize and skip_same_sized == True :
            sys.stderr.write("%s is up to date, skipping.\n" % local_filename)
        else:
            sys.stderr.write("Downloading %s from %s, saving as %s …\n" % \
                (remote_filename, server, local_filename))

            with open(local_filename, 'wb') as f:
                p = progressbar.ProgressBar(maxval=remote_filesize)

                def callback(chunk):
                    f.write(chunk)
                    p.update(p.currval + len(chunk))

                ftp.retrbinary("RETR %s" % remote_filename, callback)

    ftp.quit()
    return downloaded_filenames


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
    archive_files = get_PubMed_XML_TAR_GZ()

    for f in archive_files:
        find_PubMed_articles_with_supplementary_materials(f)
