#!/usr/bin/python3

import time
import numpy as np
import sys
import subprocess
from random import random

# reads a sudoku from file
# columns are separated by |, lines by newlines
# Example of a 4x4 sudoku:
# |1| | | |
# | | | |3|
# | | |2| |
# | |2| | |
# spaces and empty lines are ignored

def sudoku_read(filename):
    myfile = open(filename, 'r')
    sudoku = []
    N = 0
    for line in myfile:
        line = line.replace(" ", "")
        if line == "":
            continue
        line = line.split("|")
        if line[0] != '':
            exit("illegal input: every line should start with |\n")
        line = line[1:]
        if line.pop() != '\n':
            exit("illegal input\n")
        if N == 0:
            N = len(line)
            if N != 4 and N != 9 and N != 16 and N != 25:
                exit("illegal input: only size 4, 9, 16 and 25 are supported\n")
        elif N != len(line):
            exit("illegal input: number of columns not invariant\n")
        line = [int(x) if x != '' and int(x) >= 0 and int(x) <= N else 0 for x in line]
        sudoku += [line]
    return sudoku

# print sudoku on stdout
def sudoku_print(myfile, sudoku):
    if sudoku == []:
        myfile.write("impossible sudoku\n")
    N = len(sudoku)
    for line in sudoku:
        myfile.write("|")
        for number in line:
            if N > 9 and number < 10:
                myfile.write(" ")
            myfile.write(" " if number == 0 else str(number))
            myfile.write("|")
        myfile.write("\n")

# get number of constraints for sudoku
def sudoku_constraints_number(sudoku):
    N = len(sudoku)
    count = 4 * N * N * ( 1 + N * (N - 1) / 2)
    for line in sudoku:
        for number in line:
            if number > 0:
                count += 1
    return count

# prints the generic constraints for sudoku of size N
def sudoku_generic_constraints(myfile, N):

    def output(s):
        myfile.write(s)

    # Notice that the following function only works for N = 4 or N = 9 --> fixed
    def newlit(i,j,k,N):
        output(str(i*N+j) + str(k).zfill(2) + " ")

    def newneglit(i,j,k,N):
        output("-"+ str(i*N+j) + str(k).zfill(2) + " ")

    def newcl():
        output("0\n")

    def newcomment(s):
        output("")

    if N == 4:
        n = 2
    elif N == 9:
        n = 3
    elif N == 16:
        n = 4
    elif N == 25:
        n = 5
    else:
        exit("Only supports size 4, 9, 16 and 25")

    # each cell contains a number
    for i in range(0, N):
        for j in range(0, N):   
            for number in range(1, N+1):
                newlit(i, j, number, N)
            newcl()

    # each cell contains at most one number
    for i in range(0, N):
        for j in range(0, N):
            for number in range(1, N+1):
                for number2 in range(number + 1, N+1):
                    newneglit(i, j, number, N)
                    newneglit(i, j, number2, N)
                    newcl()

    # each line contains every number once
    for i in range(0, N):
        for number in range(1, N+1):
            for j in range(0, N):
                newlit(i, j, number, N)
            newcl()

    # for each line, each number appears at most once
    for i in range(0, N):
        for number in range(1, N+1):
            for j in range(0, N):
                for j2 in range(j + 1, N):
                    newneglit(i, j, number, N)
                    newneglit(i, j2, number, N)
                    newcl()

    # each column contains every number once
    for j in range(0, N):
        for number in range(1, N+1):
            for i in range(0, N):
                newlit(i, j, number, N)
            newcl()

    # for each column, each number appears at most once
    for j in range(0, N):
        for number in range(1, N+1):
            for i in range(0, N):
                for i2 in range(i + 1, N):
                    newneglit(i, j, number, N)
                    newneglit(i2, j, number, N)
                    newcl()

    # each block contains every number once
    for i in range(0, N, n):
        for j in range(0, N, n):
            for number in range(1, N+1):
                for k in range(0, n):
                    for l in range(0, n):
                        newlit(i + k, j + l, number, N)
                newcl()

    # for each block, each number appears at most once
    for i in range(0, N, n):
        for j in range(0, N, n):
            for number in range(1, N+1):
                for k in range(0, n):
                    for l in range(0, n):
                        for k2 in range(k, n):
                            for l2 in range(l + (k2 == k), n):
                                newneglit(i + k, j + l, number, N)
                                newneglit(i + k2, j + l2, number, N)
                                newcl()

def sudoku_specific_constraints(myfile, sudoku):

    N = len(sudoku)

    def output(s):
        myfile.write(s)

    # Notice that the following function only works for N = 4 or N = 9 --> fixed
    def newlit(i,j,k,N):
        output(str(i*N+j) + str(k).zfill(2) + " ")

    def newcl():
        output("0\n")

    for i in range(N):
        for j in range(N):
            if sudoku[i][j] > 0:
                newlit(i, j, sudoku[i][j], N)
                newcl()

def sudoku_other_solution_constraint(myfile, sudoku):
    # simply add a constraint that forbids the current solution
    for i in range(len(sudoku)):
        for j in range(len(sudoku)):
            if sudoku[i][j] > 0:
                myfile.write("-" + str(i*len(sudoku)+j) + str(sudoku[i][j]).zfill(2) + " ")
    myfile.write("0\n")

def sudoku_solve(filename):
    command = "java -jar org.sat4j.core.jar sudoku.cnf"
    process = subprocess.Popen(command, shell=True,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate()
    for line in out.split(b'\n'):
        line = line.decode("utf-8")
        if line == "" or line[0] == 'c':
            continue
        if line[0] == 's':
            if line != 's SATISFIABLE':
                return []
            continue
        if line[0] == 'v':
            line = line[2:]
            units = line.split()
            if units.pop() != '0':
                exit("strange output from SAT solver:" + line + "\n")
            units = [int(x) for x in units if int(x) >= 0]
            N = len(units)
            if N == 16:
                N = 4
            elif N == 81:
                N = 9
            elif N == 256:
                N = 16
            elif N == 625:
                N = 25
            else:
                exit("strange output from SAT solver:" + line + "\n")
            sudoku = [ [0 for i in range(N)] for j in range(N)]
            # Notice that the following function only works for N = 4 or N = 9 --> fixed
            for number in units:
                # isolate last two digits
                value = number % 100
                number = number // 100
                # isolate last digit
                j = number % N
                number = number // N
                # isolate first digit
                i = number
                sudoku[i][j] = value
            return sudoku
        exit("strange output from SAT solver:" + line + "\n")
        return []

def sudoku_generate(size, cm):
    sudoku = [[0 for i in range(size)] for j in range(size)]

    # generate a first batch of 9 clues that wont create a contradiction to create some kind of random seed for the SAT solver
    for k in range(1,size+1):
        i = int(random() * size)
        j = int(random() * size)
        sudoku[i][j] = k

    # solve the sudoku with this kind of random seed
    myfile = open("sudoku.cnf", "w")
    myfile.write("p cnf "+ str(size*size) + str(size).zfill(2)  +" "+
                str(sudoku_constraints_number(sudoku))+"\n")
    sudoku_generic_constraints(myfile, size)
    sudoku_specific_constraints(myfile, sudoku)
    myfile.close()

    sudoku = sudoku_solve("sudoku.cnf")
    sudoku_print(sys.stdout, sudoku)

    if cm == True:
        rand_rmv = int(random() * size) + 1
        print("Removing " + str(rand_rmv) + " clues")
        for i in range(len(sudoku)):
            for j in range(len(sudoku)):
                if sudoku[i][j] == rand_rmv:
                    sudoku[i][j] = 0

    # remove numbers from sudoku while it produces a unique solution
    while True:
        sudoku_print(sys.stdout, sudoku)
        print(" ")
        i = int(random() * size)
        j = int(random() * size)
        save = sudoku[i][j]
        sudoku[i][j] = 0

        # solve sudoku
        myfile = open("sudoku.cnf", "w")
        myfile.write("p cnf "+ str(N*N) + str(N).zfill(2)  +" "+
                    str(sudoku_constraints_number(sudoku))+"\n")
        sudoku_generic_constraints(myfile, size)
        sudoku_specific_constraints(myfile, sudoku)
        myfile.close()

        sudoku_temp = sudoku_solve(sudoku)

        #check if sudoku_temp produces a unique solution

        myfile = open("sudoku.cnf", "a")
        sudoku_other_solution_constraint(myfile, sudoku_temp)
        myfile.close()

        sudoku_temp = sudoku_solve(sudoku)

        if sudoku_temp == []:
            continue
        else:
            print("Unique sudoku found")
            sudoku[i][j] = save
            break

    return sudoku
    
if __name__ == "__main__":
    save = open("output.txt", "w")
    save.write("Results for sudokub.py\n")
    save.write("Tested on MacBook Pro 2019 Intel i5\n")
    times = np.zeros(100)
    correct = 0
    wrong = 0

    for i in range(100):
        # start a chrono
        start = time.time()
        file = "sudoku9x9/sudoku" + str(i).zfill(2) + ".txt"
        sudoku = sudoku_read(file)
        N = len(sudoku)
        myfile = open("sudoku.cnf", "w")
        myfile.write("p cnf "+ str(N*N) + str(N).zfill(2)  +" "+
                    str(sudoku_constraints_number(sudoku))+"\n")
        sudoku_generic_constraints(myfile, N)
        sudoku_specific_constraints(myfile, sudoku)
        myfile.close()
        sudoku = sudoku_solve("sudoku.cnf")

        checkfile = "sudoku9x9-sol/sudoku" + str(i).zfill(2) + ".txt"
        check = sudoku_read(checkfile)

        # stop chrono
        end = time.time()
        times[i] = end - start

        if sudoku == check:
            #print("\033[92m" + "Sudoku " + str(i).zfill(2) + " is correct in " + str(times[i]) + " seconds" + "\033[0m")
            correct += 1
        else:
            #print("\033[91m" + "Sudoku " + str(i).zfill(2) + " is incorrect in " + str(times[i]) + " seconds" + "\033[0m")
            wrong += 1

    save.write("\n### 9x9 ###\n")
    save.write("Correct: " + str(correct) + "\n")
    save.write("Wrong: " + str(wrong) + "\n")
    save.write("Average time: " + str(np.mean(times)) + " seconds" + "\n")
    save.write("Standard deviation: " + str(np.std(times)) + " seconds" + "\n")
    save.write("Maximum time: " + str(np.max(times)) + " seconds" + "\n")
    save.write("Minimum time: " + str(np.min(times)) + " seconds" + "\n")


    times = np.zeros(10)
    correct = 0
    wrong = 0

    for i in range(10):
        # start a chrono
        start = time.time()
        file = "sudoku16x16/sudoku" + str(i).zfill(2) + ".txt"
        sudoku = sudoku_read(file)
        N = len(sudoku)
        myfile = open("sudoku.cnf", "w")
        myfile.write("p cnf "+ str(N*N) + str(N).zfill(2)  +" "+
                    str(sudoku_constraints_number(sudoku))+"\n")
        sudoku_generic_constraints(myfile, N)
        sudoku_specific_constraints(myfile, sudoku)
        myfile.close()
        sudoku = sudoku_solve("sudoku.cnf")

        checkfile = "sudoku16x16-sol/sudoku" + str(i).zfill(2) + ".txt"
        check = sudoku_read(checkfile)

        # stop chrono
        end = time.time()
        times[i] = end - start

        if sudoku == check:
            #print("\033[92m" + "Sudoku " + str(i).zfill(2) + " is correct in " + str(times[i]) + " seconds" + "\033[0m")
            correct += 1
        else:
            #print("\033[91m" + "Sudoku " + str(i).zfill(2) + " is incorrect in " + str(times[i]) + " seconds" + "\033[0m")
            wrong += 1

    save.write("\n### 16x16 ###\n")
    save.write("Correct: " + str(correct) + "\n")
    save.write("Wrong: " + str(wrong) + "\n")
    save.write("Average time: " + str(np.mean(times)) + " seconds" + "\n")
    save.write("Standard deviation: " + str(np.std(times)) + " seconds" + "\n")
    save.write("Maximum time: " + str(np.max(times)) + " seconds" + "\n")
    save.write("Minimum time: " + str(np.min(times)) + " seconds" + "\n")
    times = np.zeros(4)
    correct = 0
    wrong = 0

    for i in range(4):
        # start a chrono
        start = time.time()
        file = "sudoku25x25/sudoku" + str(i).zfill(2) + ".txt"
        sudoku = sudoku_read(file)
        N = len(sudoku)
        myfile = open("sudoku.cnf", "w")
        myfile.write("p cnf "+ str(N*N) + str(N).zfill(2)  +" "+
                    str(sudoku_constraints_number(sudoku))+"\n")
        sudoku_generic_constraints(myfile, N)
        sudoku_specific_constraints(myfile, sudoku)
        myfile.close()
        sudoku = sudoku_solve("sudoku.cnf")

        checkfile = "sudoku25x25-sol/sudoku" + str(i).zfill(2) + ".txt"
        check = sudoku_read(checkfile)

        # stop chrono
        end = time.time()
        times[i] = end - start

        if sudoku == check:
            #print("\033[92m" + "Sudoku " + str(i).zfill(2) + " is correct in " + str(times[i]) + " seconds" + "\033[0m")
            correct += 1
        else:
            #print("\033[91m" + "Sudoku " + str(i).zfill(2) + " is incorrect in " + str(times[i]) + " seconds" + "\033[0m")
            wrong += 1

    save.write("\n### 25x25 ###\n")
    save.write("Correct: " + str(correct) + "\n")
    save.write("Wrong: " + str(wrong) + "\n")
    save.write("Average time: " + str(np.mean(times)) + " seconds" + "\n")
    save.write("Standard deviation: " + str(np.std(times)) + " seconds" + "\n")
    save.write("Maximum time: " + str(np.max(times)) + " seconds" + "\n")
    save.write("Minimum time: " + str(np.min(times)) + " seconds" + "\n")

    save.close()