import math
import sys
import numpy as np
import pandas as pd


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

    def init_mem(self):
        """
        Hacer un vaciado de la memoria.
        """
        self.mem = ['   ' for _ in range(0, 100)]
        self.mem[0] = '001'  #: Operación de lectura.

    def get_memint(self, data):
        """
        Ya que se tiene una memoria basada en strings, se
        requiere la conversión de string a int.
        """
        return int(self.get_mem(data))

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
        return self.mem[data]

    def set_mem(self, addr, data):
        """
        Escribir en un espacio en memoria.
        """
        self.chk_addr(addr)
        self.show()
        self.mem[addr] = self.pad(data)

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

    def opcode_10(self, data):
        """ Mult """
        self.acc = self.get_memint(data)


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

    def read_deck(self, fname):
        """
        Lectura de una lista de instrucciones(.txt).
        """
        self.reader = [s.rstrip('\n') for s in open(fname, 'r').readlines()]
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
        self.set_mem(data, self.get_input())

    def opcode_5(self, data):
        """ OUTPUT """
        self.stdout(self.get_mem(data))


class CPU(object):
    """
    Clase que representa el "CPU".
    """

    def __init__(self):
        self.init_cpu()
        self.reset()
        try:
            self.init_mem()
        except AttributeError:
            raise ConfigurationError('Realizar herencia de los 3 componentes en un solo objeto.')
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

    def fetch(self):
        """
        Este método recupera una instrucción desde la dirección de memoria apuntada por puntero del programa
        Then we increment the program pointer.
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
            print("NAME:", self.nmonics[opcode], "VALUE:", data)
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
        """ Test Accumulator Contents """
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


def main():
    try:
        c = VonNeuman()
        deck = 'prog1.txt'  #: Cuenta hasta 10.
        if len(sys.argv) > 1:
            deck = sys.argv[1]
        c.read_deck(deck)
        c.run()
    except ConfigurationError as e:
        print("Configuration Error: {0}}".format(e))
    except CPUException as e:
        # Here we trap all exceptions which can be triggered by user code, and display an error to the end-user.
        print("IR: {0}\tPC: {1}\tACC: {2}".format(c.ir, c.pc, c.acc))
        print(str(e))
    except:
        # For every other exceptions, which are normally Python related, we display it.
        print("IR: {0}\nPC: {1}\nOutput: {2}\n".format(c.ir, c.pc, c.format_output()))
        raise


if __name__ == '__main__':
    main()
