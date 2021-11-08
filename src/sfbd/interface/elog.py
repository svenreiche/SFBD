import elog

def write(text, Title = 'Test', Application = 'SFBD-Module', Attachment = None):
    """
    Generates an entry in the electronic logbook of SwissFEL Commisisoning Data
    :param text:  The text to be placed in the log book
    :param Title: Title of the log book entry
    :param Application: Name of application which generates the log book entry
    :param Attachment: List of attachments to be added to the log book (mostly plots)
    :return: Message ID of log book entry
    """

    # supplemental  info
    Author = 'sfop'
    Category  = 'Measurement' # Info or Measurement
    System = 'Beamdynamics'  # Beamdynamics, Operation, Controls

    dict_att = {'Author': Author, 'Application': Application, 'Category': Category, 'Title': Title, 'System': System}
    print('\nLog book entry generated')

    logbook = elog.open('https://elog-gfa.psi.ch/SwissFEL+commissioning+data/', user='robot', password='robot')
    return logbook.post(text, attributes=dict_att, attachments=Attachment)



