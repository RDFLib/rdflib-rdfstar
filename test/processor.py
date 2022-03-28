
import re

f = open("turtle-star/turtle-star-syntax-nested-02.ttl", "rb")
rdbytes = f.read()
f.close()
rdbytes_processing = rdbytes.decode("utf-8")

 #https://stackoverflow.com/questions/4284991/parsing-nested-parentheses-in-python-grab-content-by-level https://stackoverflow.com/questions/14952113/how-can-i-match-nested-brackets-using-regex https://stackoverflow.com/questions/11404482/recursive-descent-parser-and-nested-parentheses
current_quotation = []
def myHash(text:str):
  hash=0
  for ch in text:
    hash = ( hash*281  ^ ord(ch)*997) & 0xFFFFFFFF
  return hash
  # https://stackoverflow.com/questions/27522626/hash-function-in-python-3-3-returns-different-results-between-sessions
def ParseNestedParen(string, level):
    """
    Generate strings contained in nested (), indexing i = level
    """
    if len(re.findall("\(", string)) == len(re.findall("\)", string)):
        LeftRightIndex = [x for x in zip(
        [Left.start()+1 for Left in re.finditer('\(', string)],
        reversed([Right.start() for Right in re.finditer('\)', string)]))]

    elif len(re.findall("\(", string)) > len(re.findall("\)", string)):
        return ParseNestedParen(string + ')', level)

    elif len(re.findall("\(", string)) < len(re.findall("\)", string)):
        return ParseNestedParen('(' + string, level)

    else:
        return 'fail'

    return [string[LeftRightIndex[level][0]:LeftRightIndex[level][1]]]

def parse_to_rdf(string1, current_quotation):
    string1 = string1.replace("\n","")
    string1 = string1.replace("\r","")
    if string1[0] == " ":
        string1 = string1[1:]
    if string1[-1] == " ":
        print(string1, len(string1)-1)
        string1 = string1[:-1]
    # print("now6",string1)
    if not(len(current_quotation)==0):
        my_value = myHash(string1)
        not_in = True
        for x in current_quotation:
            if x[0] == string1:
                pass
                not_in = False
        if not_in:
            current_quotation.insert(0, [string1, myHash(string1)])

        not_in = True
        for x in current_quotation:
            # print(x,"wadawdad","okokoko","a","?")

            if x[0] == string1:
                pass
                not_in = False

            elif x[0] in string1:
                print("ok")
                if "(" in x[0]:
                    match ="("+" " + x[0] + ")"
                else:
                    match="("+x[0]+" "+")"

                if "(" in x[0]:
                    string1=string1.replace(match,":" + str(x[1]))
                else:
                    string1= string1.replace(match,":" + str(x[1]))
                print(string1)
                break


    else:
        my_value = myHash(string1)
        # print("ok")
        current_quotation.insert(0, [string1,myHash(string1)])


    splitz = string1.split(" ")
    print(current_quotation)
    subject = splitz[0]
    predicate = splitz[1]
    object = splitz[2]
    # :rei-1
    #a rdf:Statement ;
    #rdf:subject :s ;
    #rdf:predicate :p ;
    #rdf:object :o ;
    #.

    next_rdf_object = ":" + str(my_value) + '\n' + "    a rdf:Statement ;\n"+"    rdf:subject "+subject+' ;\n'+"    rdf:predicate "+predicate+" ;\n"+"    rdf:object "+object+" ;\n"+".\n\r"
    return next_rdf_object

start_processing =  False



def RDFstarParsings(rdbytes_p):
    rdf_resultspp = ""
    current_processing = ""
    for x in range(0, len(rdbytes_p)-1):
        if (not rdbytes_p[x] == '.'):
            current_processing+=rdbytes_p[x]
        else:
            number_brack = current_processing.count("<<")
            print(number_brack)
            ts = current_processing.replace("<<", "(")
            outcome_s = ts.replace(">>",")")

            if outcome_s[0] == "P":
                # print(len(outcome_s)-1)
                for z in range(0, len(outcome_s)-1):
                    # print(z)
                    if outcome_s[z] == '\n':
                        rdf_resultspp+= outcome_s[0:z+2]
                        rdf_resultspp+="PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> \n"
                        outcome_s = outcome_s[z+2:len(outcome_s)        ]


                        break
                print(outcome_s)

                if number_brack==0:
                    rdf_resultspp += parse_to_rdf(outcome_s,current_quotation)
                else:
                    for y in range(number_brack-1,-1, -1):

                        # print(y)
                        nested = ParseNestedParen(outcome_s,y)
                        rdf_resultspp += parse_to_rdf(nested[0],current_quotation)
                    rdf_resultspp += parse_to_rdf(outcome_s,current_quotation)


                # print(parse_to_rdf(outcome_s,current_quotation))
                pass
            else:
                # print(parse_parentheses(outcome_s))
                # outcomet = parse_parentheses(outcome_s)

                print(outcome_s)

                if number_brack==0:
                    rdf_resultspp += parse_to_rdf(outcome_s,current_quotation)

                else :

                    for y in range(number_brack-1,-1, -1):

                        # print(y)
                        nested = ParseNestedParen(outcome_s,y)
                        rdf_resultspp += parse_to_rdf(nested[0],current_quotation)
                        rdf_resultspp += parse_to_rdf(outcome_s,current_quotation)

            # process(current_processing)
            current_processing = ""

            print(rdf_resultspp)

    rdbytes_2 = bytes(rdf_resultspp, 'utf-8')
    print(rdbytes_2)

    return rdbytes_2



rdfstar_results = RDFstarParsings(rdbytes_processing)

print(rdfstar_results)
#
#
