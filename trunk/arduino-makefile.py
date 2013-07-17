#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  arduino-makefile.py
#  
#  Copyright 2013 Bernd Wilske <news@nfix.de>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  

# Aufrufparameter:
# -bBordname  z.B. -battiny84-8
# -pProgrammer z.B. -pusptinyisp

import sys,os,os.path,optparse
from string import Template

#Einstellungen
ARDUINO_DIR='/usr/share/arduino'

ARDUINO_DIRS = (os.path.expanduser('~/sketchbook/'),ARDUINO_DIR)

def parameter():
    parser=optparse.OptionParser(usage='%prog [optionen] [projektname]')
    parser.add_option('-b','--board',dest='board',help='Name des Boards')
    parser.add_option('-p','--programmer',dest='programmer',help='Name des Programmers')
    parser.add_option('-B',type='int',dest='programmer_clock',help='Clock-Frequenz des Programmers')
    parser.add_option('--list',action="store_true",dest='listmode',default=False,help='Namen der Boards und Programmer auflisten')
    parser.add_option('--param',action="store_true",dest='param',default=False,help=u'Alle möglichen Parameter für das Template ausgeben')
    parser.add_option('--value',action='store_true',dest='value', default=False,help=u'Alle Parameter mit ihren Werten ausgeben')
    return parser.parse_args()

def listen():
    print 'Boards:     ',', '.join(sorted(list_items('boards.txt'),key=str.lower))
    print 'Programmer: ',', '.join(sorted(list_items('programmers.txt'),key=str.lower))
    return 0

def find_template():
    return os.path.join(os.path.dirname(os.path.realpath(__file__)),'arduino-makefile.template')

def path_lib(board):
    core=board['build_core'].split(':')
    if len(core)==2 and core[0]=='arduino':
        return os.path.join(ARDUINO_DIR,'hardware/arduino/cores',core[1])
    else:
        return os.path.join(os.path.dirname(board['board_txt']),'cores',core[0])
        
def path_lib_pin(board):
    return os.path.join(os.path.dirname(board['board_txt']),'variants',board['build_variant'])

def core(board):
    prefix=None
    def _verz(datei):
        if prefix:
            return os.path.join(prefix,datei)
        else:
            return datei
            
    objects=[]
    for (verz,prefix) in ((path_lib_pin(board),None),(path_lib(board),'avr-libc'),(path_lib(board),None)):
        if prefix:
            verz=os.path.join(verz,prefix)
        if os.path.exists(verz):
            dd=os.listdir(verz)
            objects.extend(filter(lambda datei: os.path.splitext(datei)[1] in ['.c','.cpp'],dd))
    return objects

def find_dateien(dateiname):
    b=[]
    for d in ARDUINO_DIRS:
        hardware=os.path.join(d,'hardware')
        if os.path.exists(hardware):
            for root,verz,dateien in os.walk(hardware):
                if dateiname in dateien:
                    b.append(os.path.join(root,dateiname))
    return b
    
def list_items(dateinamen):
    result=[]
    for txt in find_dateien(dateinamen):
        f=open(txt,'r')
        for z in f:
            e=z.strip().split('.',1)[0]
            if (len(e)>0) & (e.find('#')!=0) & (e not in result): result.append(e)
        f.close()
    return result
    
def find_item(dateiname,itemname,prefix):
    result={}
    for txt in find_dateien(dateiname):
        f=open(txt,'r')
        for z in f:
            e=z.strip().split('.',1)
            if e[0]==itemname:
                result[prefix+'txt']=txt
                e=e[-1].split('=',1)
                if e[0]=='name': e[0]=prefix+'name'
                result[e[0].replace('.','_')]=e[1]
        f.close()
        if len(result)>0: break
    if len(result)>0:
        return result
        
def find_board(opt):
    if not opt.board: 
        print 'Parameter -b fehlt'
    else:
        b=find_item('boards.txt',opt.board,'board_')
        if b:
            return b
        else:
            print 'Board %s wurde nicht gefunden' % opt.board

def find_programmer(opt):
    if not opt.programmer:
        print 'Paramteter -p fehlt'
    else:
        p=find_item('programmers.txt',opt.programmer,'programmer_')
        if p:
            return p
        else:
            print 'Programmer %s wurde nicht gefunden' % opt.programmer

def find_projekt():
    projekt=os.getcwd().split('/')[-1]+'.ino'
    if os.path.exists(projekt):
        return projekt
    else:
        print 'Projekt %s nicht gefunden' % projekt

def search_datei_h(lib):
    for libraries in ARDUINO_DIRS:
        libraries=os.path.join(libraries,'libraries',lib)
        if os.path.exists(libraries):
            return libraries

def find_libs(projekt):
    libs={}
    lib=open(projekt,'r')
    for s in lib:
        s =s.split('#include')
        if not s[0] and len(s)==2:
            s=s[1].strip()
            if s[0]=='<' and s[-3:]=='.h>' :
                s=s[1:-3]
                sp=search_datei_h(s) 
                if sp:
                    libs[s]=sp
                    if os.path.exists(os.path.join(sp,'utility')):
                        libs['/'.join((s,'utility'))]=os.path.join(sp,'utility')
    lib.close()
    return libs
        
def build_path(opt):
    return 'build-'+opt.board

def info(opt,board,programmer,projekt,libs):
    print 'Board:        ', board['board_name']
    print 'Prozessor:    ',board['build_mcu']
    print 'Frequenz:     ',board['build_f_cpu']
    print
    print 'Programmer:   ', programmer['programmer_name']
    print 'Protokoll:    ', programmer['protocol']
    print
    print 'Projekt:      ', projekt
    print 'Build:        ', build_path(opt)
    print 'Libs:         ', ' '.join(sorted(libs,key=str.upper))
    print
    
def info_param(params):
    print 'Parameter: ',', '.join(sorted(params.keys()))    

def info_param_value(params):
    print 'Parameter: '
    for k in sorted(params.keys()):
        print '    %s = %s' % (k,params[k])

def params(opt,board,programmer,projekt,libs):
    p={'arduino_dir': ARDUINO_DIR,'program' : os.path.splitext(projekt)[0],'board': opt.board,'programmer': opt.programmer, 'lib': path_lib(board), 'lib_pin': path_lib_pin(board)}
    if opt.programmer_clock:
        p['programmer_clock']=opt.programmer_clock
    p.update(board)
    p.update(programmer)
    p['include']= ' \\\n\t\t\t'.join(map(lambda i: '\t%s' % i,libs.values()))
    p['libraries']=' '.join(libs.keys())
    p['libraries_path']=os.path.join(ARDUINO_DIRS[1],'libraries')
    p['libraries_user_path']=os.path.join(ARDUINO_DIRS[0],'libraries')
    p['core']=' '.join(core(board))
    return p
    
def template_erstellen(params):
    templatefile=open(find_template(),'r')
    make=open(os.path.join(os.getcwd(),'makefile'),'w')
    for s in templatefile:
        make.write(Template(s).substitute(params))
    make.close()
    templatefile.close()
    

def main():
    (opt,args)=parameter()
    if opt.listmode: listen()
    else:
        board=find_board(opt)
        programmer=find_programmer(opt)
        if board and programmer:
            projekt=find_projekt()
            if projekt:
                libs=find_libs(projekt)
                info(opt,board,programmer,projekt,libs)
                par=params(opt,board,programmer,projekt,libs)
                if opt.param:
                    info_param(par)
                else:
                    if opt.value:
                        info_param_value(par)
                    else:
                        template_erstellen(par)
                        #os.system('make')

    return 0

if __name__ == '__main__':
    main()

