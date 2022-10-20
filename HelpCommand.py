


class HelpCommand:
    def __init__(self, 
        name: str,
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
        print("{:<20}:{}".format(self.name, self.desc))
    
    def print_long(self, advanced = False):
        if self.is_advanced and not advanced:
            return
        print("{:<20}:{}".format(self.name, self.desc))
        if len(self.args_desc) > 0:
            print("Arguments:")
            for j in self.args_desc:
                print("    ", j)
        print("Example:", self.example)
    
        