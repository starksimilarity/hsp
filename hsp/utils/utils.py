from optparse import OptionParser


def parseargs():
    """Parses arguments from the command line.
    """
    p = OptionParser()
    p.add_option("-P", dest="password", help="Password for msfrpcd", default="password")
    p.add_option(
        "-S", dest="ssl", help="Use SSL to connect to msfrpcd", default=True
    )  # BUG: make this true/false
    p.add_option("-U", dest="username", help="Username for msfrpcd", default="msf")
    p.add_option(
        "-a",
        dest="server",
        help="IP address of the msfrpcd server",
        default="127.0.0.1",
    )
    p.add_option("-p", dest="port", help="Listening port for msfrpcd", default=55553)
    o, a = p.parse_args()

    return o


def parseconfig(filename):
    """Opens a configuration file and returns a dictionary of parameters

    Format of the config file is "history_filename:file_format #comment"
    Lines that begin with # are ignored
    Whitespace lines are ignored
    
    Parameters
    ----------
    filename : str
        Filename of the config file to open

    Returns
    -------
    options : dict
        Dictionary of options set by the config file
    """
    files = {}
    with open(filename, "r+") as infi:
        for line in infi:
            if "#" in line:
                line, comment, *_ = line.split("#")

            if line:
                try:
                    filename, file_format = line.split(":")
                    file_format = file_format.strip()
                    if not file_format:
                        file_format = None
                    files[filename] = file_format
                except:
                    pass
    return files
