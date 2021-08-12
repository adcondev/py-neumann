import tkinter
from tkinter import messagebox
import math
import sys
import os
import numpy as np
import pandas as pd
import datetime

c = 1
r = 1
color = "Green"


class ConfigurationError(Exception):
    pass


class CPUException(Exception):
    pass


class MemoryOutOfRange(CPUException):
    pass


class InvalidOperation(CPUException):
    pass


class VonNeumanMemory:
    """
    Clase para controlar la memoria.
    """

    def init_mem(self, isDict=False, theDict={}):
        """
        Hacer un vaciado de la memoria.
        """
        if not isDict:
            self.mem = ['   ' for _ in range(0, 100)]
            self.mem[0] = '001'  #: Operación de lectura.
        else:
            self.mem = theDict

    def get_memint(self, data):
        """
        Ya que se tiene una memoria basada en strings, se
        requiere la conversión de string a int.
        """
        try:
            return int(self.get_mem(data))
        except:
            return 0
    def chk_addr(self, addr):
        """
        Validar que el acceso a memoria sea válido
        """
        addr = int(addr)
        if addr < 0 or addr > len(self.mem) - 1:
            raise MemoryOutOfRange('Memoria fuera de rango: {0}'.format(addr))

    def get_mem(self, data):
        """
        Acceder a un espacio en memoria.
        """
        self.chk_addr(data)
        return self.mem[data].get()

    def set_mem(self, addr, data):
        """
        Escribir en un espacio en memoria.
        """
        self.chk_addr(addr)
        # self.show()
        self.mem[addr].delete(0, tkinter.END)
        self.mem[addr].insert(tkinter.INSERT, self.pad(data))

    def show(self):
        print(pd.DataFrame(np.array(self.mem).reshape(10, 10).T))

    @staticmethod
    def pad(data, length=3):
        """
        Hacer un padding de ceros para que el dato sea adecuado para la memoria.
        """
        orig = int(data)
        padding = '0' * length
        data = '{0}{1}'.format(padding, abs(orig))
        if orig < 0:
            return '-' + data[-length:]
        return data[-length:]

    def opcode_1(self, data):
        """ Clear and Add """
        self.acc = self.get_memint(data)

    def opcode_2(self, data):
        """ Add """
        self.acc += self.get_memint(data)

    def opcode_6(self, data):
        """ Store """
        self.set_mem(data, self.acc)

    def opcode_7(self, data):
        """ Subtract """
        self.acc -= self.get_memint(data)


class VonNeumanIO:
    """
    Clase para control de IO.
    """

    def init_input(self):
        """
        Inicializar la lectura de entrada.
        """
        self.reader = []  #: Se accede a este arreglo una vez iniciada la lectura.

    def init_output(self):
        """
        Inicializar la escritura de salida.
        """
        self.output = []

    def read_deck(self, fname, isFile=True):
        """
        Lectura de una lista de instrucciones(.txt).
        """
        if isFile:
            self.reader = [s.rstrip('\n') for s in open(fname, 'r').readlines()]
        else:
            self.reader = fname
        self.reader.reverse()

    def format_output(self):
        """
        Formato de salida, por renglones.
        """
        return '\n'.join(self.output)

    def get_input(self):
        """
        Se realiza una lectura de la lista de entrada.
        """
        try:
            return self.reader.pop()
        except IndexError:
            # Se podrían escribir las instrucciones manualmente.
            return input('INP: ')[:3]

    def stdout(self, data):
        """
        Añadir datos a la lista de salida.
        """
        self.output.append(data)

    def opcode_0(self, data):
        """ INPUT """
        global c
        reader.delete(str(c) + ".0", str(c) + ".5")
        reader.edit_reset()
        self.set_mem(data, self.get_input())
        c = c + 1

    def opcode_5(self, data):
        """ OUTPUT """
        global r
        output.insert(str(r) + ".0", str(self.get_mem(data)) + "\n")
        self.stdout(self.get_mem(data))
        r = r + 1


class CPU(object):
    """
    Clase que representa el "CPU".
    """

    def __init__(self):
        self.init_cpu()
        self.reset()
        # try:
        #   self.init_mem()
        # except AttributeError:
        #   raise ConfigurationError('Realizar herencia de los 3 componentes en un solo objeto.')
        try:
            self.init_input()
            self.init_output()
        except AttributeError:
            raise ConfigurationError('Realizar herencia de los 3 componentes en un solo objeto.')

    def reset(self):
        """
        Hacer reset a los registros del CPU.
        """
        self.pc = 0  #: Contador de programa
        self.ir = 0  #: Registro de instrucción
        self.acc = 0  #: Acumulador
        self.running = False  #: Run or Halt?

    def init_cpu(self):
        """
        Este método enlista los códigos de operación en forma de diccionario.
        Permite realizar una estructura de tipo case/select.
        Se tiene un allamado de uno a uno, el opcode representa la key y la función
        el item.
        """
        self.nmonics = {0: "INP", 1: "CLA", 2: "ADD", 3: "TAC", 4: "SFT", 5: "OUT", 6: "STO", 7: "SUB", 8: "JMP",
                        9: "HRS"}
        self.__opcodes = {}
        classes = [self.__class__]  #: Enlista todas las clases que representan el objeto.
        while classes:
            cls = classes.pop()  # Obtiene el valor de alguna de las clases
            if cls.__bases__:  # Obtiene las clases bases de las clases y las enlista
                classes = classes + list(cls.__bases__)
            for name in dir(cls):  # Retorna los atributos válidos del objeto cls.
                if name[:7] == 'opcode_':  # Solo necesitamos los opcodes.
                    try:
                        opcode = int(name[7:])
                    except ValueError:
                        raise ConfigurationError('Opcodes deben ser numéricos, opcode inválido: {0}'.format(name[7:]))
                    self.__opcodes.update({opcode: getattr(self, 'opcode_{0}'.format(opcode))})  # Se actualiza el
                    # diccionario, cuando se llame determinado opcode en el diccionario, se realizará su acción.

    def fetch(self, isReturn=False):
        """
        Este método recupera una instrucción desde la dirección de memoria apuntada por puntero del programa.
        Luego se incrementa el valor del contador de programa.
        """
        self.ir = self.get_memint(self.pc)
        self.pc += 1

    def process(self):
        """
        Procesa un solo opcode desde el PC actual.
        Este método es el que se repite a manera de loop.
        """

        self.fetch()
        opcode, data = int(math.floor(self.ir / 100)), self.ir % 100
        if opcode in self.__opcodes:
            print("IR: {0}\tPC: {1}\tACC: {2}".format(self.ir, self.pc, self.acc))
            accEntry.delete(0, tkinter.END)
            accEntry.insert(0, str(self.acc))
            opcodeEntry.delete(0, tkinter.END)
            opcodeEntry.insert(0, str(opcode))
            print("NAME:", self.nmonics[opcode], "VALUE:", data)
            operandEntry.delete(0, tkinter.END)
            operandEntry.insert(0, self.nmonics[opcode])
            self.__opcodes[opcode](data)
        else:
            raise InvalidOperation('Opcode inválido: {0}'.format(opcode))

    def run(self, pc=None):
        """ Realiza el código en memoria hasta el opcode de halt/reset """
        if pc:
            self.pc = pc
        self.running = True
        while self.running:
            self.process()
        print("Output:\n{0}".format(self.format_output()))
        self.init_output()


class VonNeuman(CPU, VonNeumanMemory, VonNeumanIO):
    """
    Opcodes necesarios para funcionar.
    """

    def opcode_3(self, data):
        """ Conditional Jump """
        if self.acc < 0:
            self.pc = data

    def opcode_4(self, data):
        """ Shift """
        x, y = int(math.floor(data / 10)), int(data % 10)
        for _ in range(0, x):
            self.acc = (self.acc * 10) % 10000
        for _ in range(0, y):
            self.acc = int(math.floor(self.acc / 10))

    def opcode_8(self, data):
        """ Unconditional Jump """
        self.set_mem(99, self.pc + 800)  # Función de retorno.
        self.pc = data

    def opcode_9(self, data):
        """ Halt and Reset operation """
        self.reset()


top = tkinter.Tk()
top.geometry("750x600")

vonNeu = VonNeuman()

# BOTONES
offsetX1 = 360
offsetY1 = 500
# LISTAS
offsetX2 = 125
offsetY2 = 350
# Tamaño de memoria
height = 10
width = 10
cells = {}


def helloworld():
    messagebox.showinfo("hello", "hola")


def loadDeck():
    vonNeu.running = True  #: Run or Halt?
    vonNeu.pc = int(pcEntry.get())  #: Contador de programa
    vonNeu.ir = int(insRegEntry.get())  #: Registro de instrucción
    vonNeu.acc = int(accEntry.get())  #: Acumulador
    vonNeu.init_mem(True, cells)
    if vonNeu.mem[0].get() == "":
        vonNeu.mem[0].insert(tkinter.INSERT, "001")
    vonNeu.mem[vonNeu.pc].configure({"background": "Green"})
    reader.insert(tkinter.INSERT, deck.get("1.0", tkinter.END))
    instList = deck.get("1.0", tkinter.END).split("\n")
    instList.pop()
    vonNeu.read_deck(instList, False)
    print("VoNeu Reader:", vonNeu.reader)


def loadfromDeck():
    vonNeu.running = True  #: Run or Halt?
    vonNeu.pc = int(pcEntry.get())  #: Contador de programa
    vonNeu.ir = int(insRegEntry.get())  #: Registro de instrucción
    vonNeu.acc = int(accEntry.get())  #: Acumulador
    vonNeu.init_mem(True, cells)
    if vonNeu.mem[0].get() == "":
        vonNeu.mem[0].insert(tkinter.INSERT, "001")
    vonNeu.mem[vonNeu.pc].configure({"background": "Green"})
    with open(txtEntry.get(), "r") as txtr:
        data = txtr.readlines()
    for x in data:
        deck.insert(tkinter.END, x)
    instList = deck.get("1.0", tkinter.END).split("\n")
    instList.pop()
    vonNeu.read_deck(instList, False)
    txtEntry.delete(0, 'end')
    print("VoNeu Reader:", vonNeu.reader)


def resetApp():
    python = sys.executable
    os.execl(python, python, *sys.argv)


def timeStep():
    if vonNeu.running:
        vonNeu.mem[vonNeu.pc].configure({"background": "white"})
        vonNeu.process()
        vonNeu.mem[vonNeu.pc].configure({"background": "Green"})
        pcEntry.delete(0, tkinter.END)
        pcEntry.insert(tkinter.INSERT, str(vonNeu.pc))
        insRegEntry.delete(0, tkinter.END)
        insRegEntry.insert(tkinter.INSERT, str(vonNeu.ir))


def fastStep():
    timeStep()
    top.after(40, fastStep)


def slowStep():
    timeStep()
    top.after(250, slowStep)


def haltReset():
    if vonNeu.running:
        vonNeu.running = False
    else:
        vonNeu.running = True


def cleanMem():
    for i in range(height):
        for j in range(width):
            cells[i * 10 + j].delete(0, 'end')


reset = tkinter.Button(top, text="Reset", command=resetApp, padx=0, pady=0)
cleanMem = tkinter.Button(top, text="Clean Mem", command=cleanMem)
step = tkinter.Button(top, text="Step", command=timeStep)
runSlow = tkinter.Button(top, text="Slow", command=slowStep)
runFast = tkinter.Button(top, text="Fast", command=fastStep)
halt = tkinter.Button(top, text="Halt", command=haltReset)
load = tkinter.Button(top, text="Load", command=loadDeck)
loadfrom = tkinter.Button(top, text="Txt", command=loadfromDeck)

reset.place(x=offsetX1 - 40, y=offsetY1)
cleanMem.place(x=offsetX1 + 50, y=offsetY1)
step.place(x=offsetX1 - 50, y=offsetY1 + 30)
runSlow.place(x=offsetX1, y=offsetY1 + 30)
runFast.place(x=offsetX1 + 50, y=offsetY1 + 30)
halt.place(x=offsetX1 + 100, y=offsetY1 + 30)
load.place(x=offsetX2 + 70, y=offsetY2 + 25)
loadfrom.place(x=offsetX2 + 70, y=offsetY2 + 55)
#
deck = tkinter.Text(top, width=6, height=10, undo=False)
reader = tkinter.Text(top, width=6, height=10, undo=False)
output = tkinter.Text(top, width=6, height=10, undo=False)

deck.place(x=offsetX2, y=offsetY2)
reader.place(x=offsetX2 + 125, y=offsetY2)
output.place(x=offsetX2 + 400, y=offsetY2)

#
deckLabel = tkinter.Label(top, text="Instrucciones", font='Helvetica 9 bold')
readerLabel = tkinter.Label(top, text="Reader", font='Helvetica 9 bold')
cpuLabel = tkinter.Label(top, text="CPU", font='Helvetica 9 bold')
outputLabel = tkinter.Label(top, text="Output", font='Helvetica 9 bold')
decoderLabel = tkinter.Label(top, text="Decodificador de Inst", font='Helvetica 9 bold')
memLabel = tkinter.Label(top, text="Memoria", font='Helvetica 14 bold')

deckLabel.place(x=offsetX2 - 10, y=offsetY2 - 25)
readerLabel.place(x=offsetX2 + 130, y=offsetY2 - 25)
cpuLabel.place(x=offsetX2 + 260, y=offsetY2 - 25)
outputLabel.place(x=offsetX2 + 400, y=offsetY2 - 25)
decoderLabel.place(x=offsetX2 + 225, y=offsetY2 + 30)
memLabel.place(x=320, y=15)

#
pcLabel = tkinter.Label(top, text="PC:")
insRegLabel = tkinter.Label(top, text="Registro de Inst:")
opcodeLabel = tkinter.Label(top, text="Opcode:")
operandLabel = tkinter.Label(top, text="Operando:")
accLabel = tkinter.Label(top, text="Acumulador:")
txtLabel = tkinter.Label(top, text="File:")

pcLabel.place(x=offsetX2 + 240, y=offsetY2)
insRegLabel.place(x=offsetX2 + 210, y=offsetY2 + 50)
opcodeLabel.place(x=offsetX2 + 190, y=offsetY2 + 75)
operandLabel.place(x=offsetX2 + 285, y=offsetY2 + 75)
accLabel.place(x=offsetX2 + 220, y=offsetY2 + 110)
txtLabel.place(x=offsetX1 - 210, y=offsetY1 + 25)

for i in range(height):
    instLabel = tkinter.Label(top, text=str(i) + " " + vonNeu.nmonics[i])
    colLabel = tkinter.Label(top, text="0" + str(i))
    rowLabel = tkinter.Label(top, text=str(i) + "0")
    instLabel.place(x=650, y=i * 25 + 70)
    rowLabel.place(x=i * 50 + 120, y=45)
    colLabel.place(x=90, y=i * 25 + 70)
    for j in range(width):
        memoryGrid = tkinter.Entry(top, width=6)
        memoryGrid.place(x=i * 50 + 120, y=j * 25 + 70)
        cells[i * 10 + j] = memoryGrid

#
pcEntry = tkinter.Entry(top, width=6)
pcEntry.insert(tkinter.INSERT, "0")
insRegEntry = tkinter.Entry(top, width=6)
insRegEntry.insert(tkinter.INSERT, "0")
opcodeEntry = tkinter.Entry(top, width=6)
operandEntry = tkinter.Entry(top, width=6)
accEntry = tkinter.Entry(top, width=8)
accEntry.insert(tkinter.INSERT, "0")
txtEntry = tkinter.Entry(top, width=10)

pcEntry.place(x=offsetX2 + 270, y=offsetY2)
insRegEntry.place(x=offsetX2 + 300, y=offsetY2 + 50)
opcodeEntry.place(x=offsetX2 + 245, y=offsetY2 + 75)
operandEntry.place(x=offsetX2 + 350, y=offsetY2 + 75)
accEntry.place(x=offsetX2 + 295, y=offsetY2 + 110)
txtEntry.place(x=offsetX1 - 180, y=offsetY1 + 25)

top.mainloop()
