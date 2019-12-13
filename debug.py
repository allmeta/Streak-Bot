from datetime import datetime


def format_date():
    return datetime.now().ctime()


def write(msg):
    print(msg, file='log.txt')


def info(msg):
    prefix = '***INFO***'
    write(f'{prefix} {format_date()}: {msg}')


def warning(msg):
    prefix = '***WARNING***'
    write(f'{prefix} {format_date}: {msg}')


def forbidden(msg):
    prefix = '***FORBIDDEN***'
    write(f'{prefix} {format_date}: {msg}')