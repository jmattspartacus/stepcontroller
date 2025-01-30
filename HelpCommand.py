import textwrap


class HelpCommand:
    def __init__(self, 
        name: list,
        func,
        arg_types,
        arg_opt: bool,
        is_advanced: bool,
        desc: str,
        arg_desc,
        example: str):
        self.name        = name
        self.func        = func
        self.desc        = desc
        self.arg_types   = arg_types
        self.arg_desc    = arg_desc
        self.arg_opt     = arg_opt
        self.is_advanced = is_advanced
        self.example     = example

    def print_short(self, advanced = False):
        if self.is_advanced and not advanced:
            return
        formatted_desc = textwrap.fill(self.desc, width = 80)
        namestr = ""
        for i in range(len(self.name)):
            namestr += "%s"%(self.name[i])
            if (i < len(self.name)-1):
                namestr+="/"

        print("%20s  \033[2;39m:  "%(namestr), end="")
        print(formatted_desc.replace("\n", "\n%20s     "%(" ")))
        print("\033[0m",end="")   
 
    def print_long(self, advanced = False):
        if self.is_advanced and not advanced:
            return

        formatted_desc = textwrap.fill(self.desc, width = 80)
        namestr = ""
        for i in range(len(self.name)):
            namestr += "%s"%(self.name[i])
            if (i < len(self.name)-1):
                namestr+="/"

        print("%20s  \033[2;39m:  "%(namestr), end="")
        print(formatted_desc.replace("\n", "\n%20s     "%(" ")))
        print("\033[0m",end="")   
        if len(self.arg_desc) > 0:
            print("Arguments:")
            for j in self.arg_desc:
                print("    ", j)
        print("Example:", self.example)
    
        
