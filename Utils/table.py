#!/usr/bin/env python
import copy
import math
import random
import re
import textwrap

import wcwidth

FRAME = 0
ALL = 1
NONE = 2
HEADER = 3

DEFAULT = 10
MSWORD_FRIENDLY = 11
PLAIN_COLUMNS = 12
MARKDOWN = 13
ORGMODE = 14
RANDOM = 20

_re = re.compile(r"\033\[[0-9;]*m")

def _get_size(text):
    lines = text.split("\n")
    height = len(lines)
    width = max(_str_block_width(line) for line in lines)
    return width, height

class Table:
    def __init__(self, field_names=None, **kwargs):
        self.encoding = kwargs.get("encoding", "UTF-8")

        self._field_names = []
        self._rows = []
        self.align = {}
        self.valign = {}
        self.max_width = {}
        self.min_width = {}
        self.int_format = {}
        self.float_format = {}
        if field_names:
            self.field_names = field_names
        else:
            self._widths = []

        self._options = ("title start end fields header border sortby reversesort "
                         "sort_key attributes format hrules vrules".split())
        self._options.extend("int_format float_format min_table_width max_table_width padding_width "
                             "left_padding_width right_padding_width".split())
        self._options.extend("vertical_char horizontal_char junction_char header_style valign xhtml "
                             "print_empty oldsortslice".split())
        self._options.extend("align valign max_width min_width".split())
        for option in self._options:
            if option in kwargs:
                self._validate_option(option, kwargs[option])
            else:
                kwargs[option] = None

        self._title = kwargs["title"] or None
        self._start = kwargs["start"] or 0
        self._end = kwargs["end"] or None
        self._fields = kwargs["fields"] or None

        if kwargs["header"] in (True, False):
            self._header = kwargs["header"]
        else:
            self._header = True
        self._header_style = kwargs["header_style"] or None
        if kwargs["border"] in (True, False):
            self._border = kwargs["border"]
        else:
            self._border = True
        self._hrules = kwargs["hrules"] or FRAME
        self._vrules = kwargs["vrules"] or ALL

        self._sortby = kwargs["sortby"] or None
        if kwargs["reversesort"] in (True, False):
            self._reversesort = kwargs["reversesort"]
        else:
            self._reversesort = False
        self._sort_key = kwargs["sort_key"] or (lambda x:x)

        self.align = kwargs["align"] or {}
        self.valign = kwargs["valign"] or {}
        self.max_width = kwargs["max_width"] or {}
        self.min_width = kwargs["min_width"] or {}
        self.int_format = kwargs["int_format"] or {}
        self.float_format = kwargs["float_format"] or {}

        self._min_table_width = kwargs["min_table_width"] or None
        self._max_table_width = kwargs["max_table_width"] or None
        if kwargs["padding_width"] is None:
            self._padding_width = 1
        else:
            self._padding_width = kwargs["padding_width"]
        self._left_padding_width = kwargs["left_padding_width"] or None
        self._right_padding_width = kwargs["right_padding_width"] or None

        self._vertical_char = kwargs["vertical_char"] or "|"
        self._horizontal_char = kwargs["horizontal_char"] or "-"
        self._junction_char = kwargs["junction_char"] or "+"

        if kwargs["print_empty"] in (True, False):
            self._print_empty = kwargs["print_empty"]
        else:
            self._print_empty = True
        if kwargs["oldsortslice"] in (True, False):
            self._oldsortslice = kwargs["oldsortslice"]
        else:
            self._oldsortslice = False
        self._format = kwargs["format"] or False
        self._xhtml = kwargs["xhtml"] or False
        self._attributes = kwargs["attributes"] or {}

    def _justify(self, text, width, align):
        excess = width - _str_block_width(text)
        if align == "l":
            return text + excess * " "
        elif align == "r":
            return excess * " " + text
        else:
            if excess % 2:
                if _str_block_width(text) % 2:
                    return (excess // 2) * " " + text + (excess // 2 + 1) * " "
                else:
                    return (excess // 2 + 1) * " " + text + (excess // 2) * " "
            else:
                return (excess // 2) * " " + text + (excess // 2) * " "

    def __getattr__(self, name):
        if name == "rowcount":
            return len(self._rows)
        elif name == "colcount":
            if self._field_names:
                return len(self._field_names)
            elif self._rows:
                return len(self._rows[0])
            else:
                return 0
        else:
            raise AttributeError(name)

    def __getitem__(self, index):
        new = Table()
        new.field_names = self.field_names
        for attr in self._options:
            setattr(new, "_" + attr, getattr(self, "_" + attr))
        setattr(new, "_align", getattr(self, "_align"))
        if isinstance(index, slice):
            for row in self._rows[index]:
                new.add_row(row)
        elif isinstance(index, int):
            new.add_row(self._rows[index])
        else:
            raise Exception(f"Index {index} is invalid, must be an integer or slice")
        return new

    def get_string(self, **kwargs):
        options = self._get_options(kwargs)

        lines = []

        if self.rowcount == 0 and (not options["print_empty"] or not options["border"]):
            return ""

        rows = self._get_rows(options)

        formatted_rows = self._format_rows(rows, options)

        self._compute_widths(formatted_rows, options)
        self._hrule = self._stringify_hrule(options)

        title = options["title"] or self._title
        if title:
            lines.append(self._stringify_title(title, options))

        if options["header"]:
            lines.append(self._stringify_header(options))
        elif options["border"] and options["hrules"] in (ALL, FRAME):
            lines.append(self._hrule)

        for row in formatted_rows:
            lines.append(self._stringify_row(row, options))

        if options["border"] and options["hrules"] == FRAME:
            lines.append(self._hrule)

        if "orgmode" in self.__dict__ and self.orgmode is True:
            tmp = list()
            for line in lines:
                tmp.extend(line.split("\n"))
            lines = ["|" + line[1:-1] + "|" for line in tmp]

        return "\n".join(lines)

    def __str__(self):
        return self.get_string()

    def _validate_option(self, option, val):
        if option == "field_names":
            self._validate_field_names(val)
        elif option in ("start", "end", "max_width", "min_width", "min_table_width", "max_table_width", "padding_width", "left_padding_width", "right_padding_width", "format",):
            self._validate_nonnegative_int(option, val)
        elif option == "sortby":
            self._validate_field_name(option, val)
        elif option == "sort_key":
            self._validate_function(option, val)
        elif option == "hrules":
            self._validate_hrules(option, val)
        elif option == "vrules":
            self._validate_vrules(option, val)
        elif option == "fields":
            self._validate_all_field_names(option, val)
        elif option in ("header", "border", "reversesort", "xhtml", "print_empty", "oldsortslice",):
            self._validate_true_or_false(option, val)
        elif option == "header_style":
            self._validate_header_style(val)
        elif option == "int_format":
            self._validate_int_format(option, val)
        elif option == "float_format":
            self._validate_float_format(option, val)
        elif option in ("vertical_char", "horizontal_char", "junction_char"):
            self._validate_single_char(option, val)
        elif option == "attributes":
            self._validate_attributes(option, val)

    def _validate_field_names(self, val):
        if self._field_names:
            try:
                assert len(val) == len(self._field_names)
            except AssertionError:
                raise Exception("Field name list has incorrect number of values, "
                                f"(actual) {len(val)}!={len(self._field_names)} (expected)")
        if self._rows:
            try:
                assert len(val) == len(self._rows[0])
            except AssertionError:
                raise Exception("Field name list has incorrect number of values, "
                                f"(actual) {len(val)}!={len(self._rows[0])} (expected)")

        try:
            assert len(val) == len(set(val))
        except AssertionError:
            raise Exception("Field names must be unique!")

    def _validate_header_style(self, val):
        try:
            assert val in ("cap", "title", "upper", "lower", None)
        except AssertionError:
            raise Exception("Invalid header style, use cap, title, upper, lower or None!")

    def _validate_align(self, val):
        try:
            assert val in ["l", "c", "r"]
        except AssertionError:
            raise Exception(f"Alignment {val} is invalid, use l, c or r!")

    def _validate_valign(self, val):
        try:
            assert val in ["t", "m", "b", None]
        except AssertionError:
            raise Exception(f"Alignment {val} is invalid, use t, m, b or None!")

    def _validate_nonnegative_int(self, name, val):
        try:
            assert int(val) >= 0
        except AssertionError:
            raise Exception(f"Invalid value for {name}: {val}!")

    def _validate_true_or_false(self, name, val):
        try:
            assert val in (True, False)
        except AssertionError:
            raise Exception(f"Invalid value for {name}! Must be True or False.")

    def _validate_int_format(self, name, val):
        if val == "":
            return
        try:
            assert isinstance(val, str)
            assert val.isdigit()
        except AssertionError:
            raise Exception(f"Invalid value for {name}! Must be an integer format string.")

    def _validate_float_format(self, name, val):
        if val == "":
            return
        try:
            assert isinstance(val, str)
            assert "." in val
            bits = val.split(".")
            assert len(bits) <= 2
            assert bits[0] == "" or bits[0].isdigit()
            assert (bits[1] == "" or bits[1].isdigit() or (bits[1][-1] == "f" and bits[1].rstrip("f").isdigit()))
        except AssertionError:
            raise Exception(f"Invalid value for {name}! Must be a float format string.")

    def _validate_function(self, name, val):
        try:
            assert hasattr(val, "__call__")
        except AssertionError:
            raise Exception(f"Invalid value for {name}! Must be a function.")

    def _validate_hrules(self, name, val):
        try:
            assert val in (ALL, FRAME, HEADER, NONE)
        except AssertionError:
            raise Exception(f"Invalid value for {name}! Must be ALL, FRAME, HEADER or NONE.")

    def _validate_vrules(self, name, val):
        try:
            assert val in (ALL, FRAME, NONE)
        except AssertionError:
            raise Exception(f"Invalid value for {name}! Must be ALL, FRAME, or NONE.")

    def _validate_field_name(self, name, val):
        try:
            assert (val in self._field_names) or (val is None)
        except AssertionError:
            raise Exception(f"Invalid field name: {val}!")

    def _validate_all_field_names(self, name, val):
        try:
            for x in val:
                self._validate_field_name(name, x)
        except AssertionError:
            raise Exception("fields must be a sequence of field names!")

    def _validate_single_char(self, name, val):
        try:
            assert _str_block_width(val) == 1
        except AssertionError:
            raise Exception(f"Invalid value for {name}! Must be a string of length 1.")

    def _validate_attributes(self, name, val):
        try:
            assert isinstance(val, dict)
        except AssertionError:
            raise Exception("attributes must be a dictionary of name/value pairs!")

    @property
    def field_names(self):
        return self._field_names

    @field_names.setter
    def field_names(self, val):
        val = [str(x) for x in val]
        self._validate_option("field_names", val)
        old_names = None
        if self._field_names:
            old_names = self._field_names[:]
        self._field_names = val
        if self._align and old_names:
            for old_name, new_name in zip(old_names, val):
                self._align[new_name] = self._align[old_name]
            for old_name in old_names:
                if old_name not in self._align:
                    self._align.pop(old_name)
        else:
            self.align = "c"
        if self._valign and old_names:
            for old_name, new_name in zip(old_names, val):
                self._valign[new_name] = self._valign[old_name]
            for old_name in old_names:
                if old_name not in self._valign:
                    self._valign.pop(old_name)
        else:
            self.valign = "t"

    @property
    def align(self):
        return self._align

    @align.setter
    def align(self, val):
        if not self._field_names:
            self._align = {}
        elif val is None or (isinstance(val, dict) and len(val) == 0):
            for field in self._field_names:
                self._align[field] = "c"
        else:
            self._validate_align(val)
            for field in self._field_names:
                self._align[field] = val

    @property
    def valign(self):
        return self._valign

    @valign.setter
    def valign(self, val):
        if not self._field_names:
            self._valign = {}
        elif val is None or (isinstance(val, dict) and len(val) == 0):
            for field in self._field_names:
                self._valign[field] = "t"
        else:
            self._validate_valign(val)
            for field in self._field_names:
                self._valign[field] = val

    @property
    def max_width(self):
        return self._max_width

    @max_width.setter
    def max_width(self, val):
        if val is None or (isinstance(val, dict) and len(val) == 0):
            self._max_width = {}
        else:
            self._validate_option("max_width", val)
            for field in self._field_names:
                self._max_width[field] = val

    @property
    def min_width(self):
        return self._min_width

    @min_width.setter
    def min_width(self, val):
        if val is None or (isinstance(val, dict) and len(val) == 0):
            self._min_width = {}
        else:
            self._validate_option("min_width", val)
            for field in self._field_names:
                self._min_width[field] = val

    @property
    def min_table_width(self):
        return self._min_table_width

    @min_table_width.setter
    def min_table_width(self, val):
        self._validate_option("min_table_width", val)
        self._min_table_width = val

    @property
    def max_table_width(self):
        return self._max_table_width

    @max_table_width.setter
    def max_table_width(self, val):
        self._validate_option("max_table_width", val)
        self._max_table_width = val

    @property
    def fields(self):
        return self._fields

    @fields.setter
    def fields(self, val):
        self._validate_option("fields", val)
        self._fields = val

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, val):
        self._title = str(val)

    @property
    def start(self):
        return self._start

    @start.setter
    def start(self, val):
        self._validate_option("start", val)
        self._start = val

    @property
    def end(self):
        return self._end

    @end.setter
    def end(self, val):
        self._validate_option("end", val)
        self._end = val

    @property
    def sortby(self):
        return self._sortby

    @sortby.setter
    def sortby(self, val):
        self._validate_option("sortby", val)
        self._sortby = val

    @property
    def reversesort(self):
        return self._reversesort

    @reversesort.setter
    def reversesort(self, val):
        self._validate_option("reversesort", val)
        self._reversesort = val

    @property
    def sort_key(self):
        return self._sort_key

    @sort_key.setter
    def sort_key(self, val):
        self._validate_option("sort_key", val)
        self._sort_key = val

    @property
    def header(self):
        return self._header

    @header.setter
    def header(self, val):
        self._validate_option("header", val)
        self._header = val

    @property
    def header_style(self):
        return self._header_style

    @header_style.setter
    def header_style(self, val):
        self._validate_header_style(val)
        self._header_style = val

    @property
    def border(self):
        return self._border

    @border.setter
    def border(self, val):
        self._validate_option("border", val)
        self._border = val

    @property
    def hrules(self):
        return self._hrules

    @hrules.setter
    def hrules(self, val):
        self._validate_option("hrules", val)
        self._hrules = val

    @property
    def vrules(self):
        return self._vrules

    @vrules.setter
    def vrules(self, val):
        self._validate_option("vrules", val)
        self._vrules = val

    @property
    def int_format(self):
        return self._int_format

    @int_format.setter
    def int_format(self, val):
        if val is None or (isinstance(val, dict) and len(val) == 0):
            self._int_format = {}
        else:
            self._validate_option("int_format", val)
            for field in self._field_names:
                self._int_format[field] = val

    @property
    def float_format(self):
        return self._float_format

    @float_format.setter
    def float_format(self, val):
        if val is None or (isinstance(val, dict) and len(val) == 0):
            self._float_format = {}
        else:
            self._validate_option("float_format", val)
            for field in self._field_names:
                self._float_format[field] = val

    @property
    def padding_width(self):
        return self._padding_width

    @padding_width.setter
    def padding_width(self, val):
        self._validate_option("padding_width", val)
        self._padding_width = val

    @property
    def left_padding_width(self):
        return self._left_padding_width

    @left_padding_width.setter
    def left_padding_width(self, val):
        self._validate_option("left_padding_width", val)
        self._left_padding_width = val

    @property
    def right_padding_width(self):
        return self._right_padding_width

    @right_padding_width.setter
    def right_padding_width(self, val):
        self._validate_option("right_padding_width", val)
        self._right_padding_width = val

    @property
    def vertical_char(self):
        return self._vertical_char

    @vertical_char.setter
    def vertical_char(self, val):
        val = str(val)
        self._validate_option("vertical_char", val)
        self._vertical_char = val

    @property
    def horizontal_char(self):
        return self._horizontal_char

    @horizontal_char.setter
    def horizontal_char(self, val):
        val = str(val)
        self._validate_option("horizontal_char", val)
        self._horizontal_char = val

    @property
    def junction_char(self):
        return self._junction_char

    @junction_char.setter
    def junction_char(self, val):
        val = str(val)
        self._validate_option("vertical_char", val)
        self._junction_char = val

    @property
    def format(self):
        return self._format

    @format.setter
    def format(self, val):
        self._validate_option("format", val)
        self._format = val

    @property
    def print_empty(self):
        return self._print_empty

    @print_empty.setter
    def print_empty(self, val):
        self._validate_option("print_empty", val)
        self._print_empty = val

    @property
    def attributes(self):
        return self._attributes

    @attributes.setter
    def attributes(self, val):
        self._validate_option("attributes", val)
        self._attributes = val

    @property
    def oldsortslice(self):
        return self._oldsortslice

    @oldsortslice.setter
    def oldsortslice(self, val):
        self._validate_option("oldsortslice", val)
        self._oldsortslice = val

    def _get_options(self, kwargs):

        options = {}
        for option in self._options:
            if option in kwargs:
                self._validate_option(option, kwargs[option])
                options[option] = kwargs[option]
            else:
                options[option] = getattr(self, "_" + option)
        return options

    def set_style(self, style):

        if style == DEFAULT:
            self._set_default_style()
        elif style == MSWORD_FRIENDLY:
            self._set_msword_style()
        elif style == PLAIN_COLUMNS:
            self._set_columns_style()
        elif style == MARKDOWN:
            self._set_markdown_style()
        elif style == ORGMODE:
            self._set_orgmode_style()
        elif style == RANDOM:
            self._set_random_style()
        else:
            raise Exception("Invalid pre-set style!")

    def _set_orgmode_style(self):
        self._set_default_style()
        self.orgmode = True

    def _set_markdown_style(self):
        self.header = True
        self.border = True
        self._hrules = None
        self.padding_width = 1
        self.left_padding_width = 1
        self.right_padding_width = 1
        self.vertical_char = "|"
        self.junction_char = "|"

    def _set_default_style(self):
        self.header = True
        self.border = True
        self._hrules = FRAME
        self._vrules = ALL
        self.padding_width = 1
        self.left_padding_width = 1
        self.right_padding_width = 1
        self.vertical_char = "|"
        self.horizontal_char = "-"
        self.junction_char = "+"

    def _set_msword_style(self):
        self.header = True
        self.border = True
        self._hrules = NONE
        self.padding_width = 1
        self.left_padding_width = 1
        self.right_padding_width = 1
        self.vertical_char = "|"

    def _set_columns_style(self):
        self.header = True
        self.border = False
        self.padding_width = 1
        self.left_padding_width = 0
        self.right_padding_width = 8

    def _set_random_style(self):
        self.header = random.choice((True, False))
        self.border = random.choice((True, False))
        self._hrules = random.choice((ALL, FRAME, HEADER, NONE))
        self._vrules = random.choice((ALL, FRAME, NONE))
        self.left_padding_width = random.randint(0, 5)
        self.right_padding_width = random.randint(0, 5)
        self.vertical_char = random.choice(r"~!@#$%^&*()_+|-=\{}[];':\",./;<>?")
        self.horizontal_char = random.choice(r"~!@#$%^&*()_+|-=\{}[];':\",./;<>?")
        self.junction_char = random.choice(r"~!@#$%^&*()_+|-=\{}[];':\",./;<>?")

    def add_row(self, row):
        if self._field_names and len(row) != len(self._field_names):
            raise Exception("Row has incorrect number of values, "
                            f"(actual) {len(row)}!={len(self._field_names)} (expected)")
        if not self._field_names:
            self.field_names = [f"Field {n + 1}" for n in range(0, len(row))]
        self._rows.append(list(row))

    def _format_value(self, field, value):
        if isinstance(value, int) and field in self._int_format:
            value = ("%%%sd" % self._int_format[field]) % value
        elif isinstance(value, float) and field in self._float_format:
            value = ("%%%sf" % self._float_format[field]) % value
        return str(value)

    def _compute_table_width(self, options):
        table_width = 2 if options["vrules"] in (FRAME, ALL) else 0
        per_col_padding = sum(self._get_padding_widths(options))
        for index, fieldname in enumerate(self.field_names):
            if not options["fields"] or (options["fields"] and fieldname in options["fields"]):
                table_width += self._widths[index] + per_col_padding
        return table_width

    def _compute_widths(self, rows, options):
        if options["header"]:
            widths = [_get_size(field)[0] for field in self._field_names]
        else:
            widths = len(self.field_names) * [0]

        for row in rows:
            for index, value in enumerate(row):
                fieldname = self.field_names[index]
                if fieldname in self.max_width:
                    widths[index] = max(widths[index], min(_get_size(value)[0], self.max_width[fieldname]), )
                else:
                    widths[index] = max(widths[index], _get_size(value)[0])
                if fieldname in self.min_width:
                    widths[index] = max(widths[index], self.min_width[fieldname])
        self._widths = widths

        if self._max_table_width:
            table_width = self._compute_table_width(options)
            if table_width > self._max_table_width:
                scale = 1.0 * self._max_table_width / table_width
                widths = [int(math.floor(w * scale)) for w in widths]
                self._widths = widths

        if self._min_table_width or options["title"]:
            if options["title"]:
                title_width = len(options["title"]) + sum(self._get_padding_widths(options))
                if options["vrules"] in (FRAME, ALL):
                    title_width += 2
            else:
                title_width = 0
            min_table_width = self.min_table_width or 0
            min_width = max(title_width, min_table_width)
            table_width = self._compute_table_width(options)
            if table_width < min_width:
                scale = 1.0 * min_width / table_width
                widths = [int(math.ceil(w * scale)) for w in widths]
                self._widths = widths

    def _get_padding_widths(self, options):
        if options["left_padding_width"] is not None:
            lpad = options["left_padding_width"]
        else:
            lpad = options["padding_width"]
        if options["right_padding_width"] is not None:
            rpad = options["right_padding_width"]
        else:
            rpad = options["padding_width"]
        return lpad, rpad

    def _get_rows(self, options):
        if options["oldsortslice"]:
            rows = copy.deepcopy(self._rows[options["start"]: options["end"]])
        else:
            rows = copy.deepcopy(self._rows)

        if options["sortby"]:
            sortindex = self._field_names.index(options["sortby"])
            rows = [[row[sortindex]] + row for row in rows]
            rows.sort(reverse=options["reversesort"], key=options["sort_key"])
            rows = [row[1:] for row in rows]

        if not options["oldsortslice"]:
            rows = rows[options["start"]: options["end"]]

        return rows

    def _format_row(self, row, options):
        return [self._format_value(field, value) for (field, value) in zip(self._field_names, row)]

    def _format_rows(self, rows, options):
        return [self._format_row(row, options) for row in rows]

    def _stringify_hrule(self, options):

        if not options["border"]:
            return ""
        lpad, rpad = self._get_padding_widths(options)
        if options["vrules"] in (ALL, FRAME):
            bits = [options["junction_char"]]
        else:
            bits = [options["horizontal_char"]]
        # For tables with no data or fieldnames
        if not self._field_names:
            bits.append(options["junction_char"])
            return "".join(bits)
        for field, width in zip(self._field_names, self._widths):
            if options["fields"] and field not in options["fields"]:
                continue
            bits.append((width + lpad + rpad) * options["horizontal_char"])
            if options["vrules"] == ALL:
                bits.append(options["junction_char"])
            else:
                bits.append(options["horizontal_char"])
        if options["vrules"] == FRAME:
            bits.pop()
            bits.append(options["junction_char"])
        return "".join(bits)

    def _stringify_title(self, title, options):

        lines = []
        lpad, rpad = self._get_padding_widths(options)
        if options["border"]:
            if options["vrules"] == ALL:
                options["vrules"] = FRAME
                lines.append(self._stringify_hrule(options))
                options["vrules"] = ALL
            elif options["vrules"] == FRAME:
                lines.append(self._stringify_hrule(options))
        bits = []
        endpoint = (options["vertical_char"] if options["vrules"] in (ALL, FRAME) else " ")
        bits.append(endpoint)
        title = " " * lpad + title + " " * rpad
        bits.append(self._justify(title, len(self._hrule) - 2, "c"))
        bits.append(endpoint)
        lines.append("".join(bits))
        return "\n".join(lines)

    def _stringify_header(self, options):

        bits = []
        lpad, rpad = self._get_padding_widths(options)
        if options["border"]:
            if options["hrules"] in (ALL, FRAME):
                bits.append(self._hrule)
                bits.append("\n")
            if options["vrules"] in (ALL, FRAME):
                bits.append(options["vertical_char"])
            else:
                bits.append(" ")
        if not self._field_names:
            if options["vrules"] in (ALL, FRAME):
                bits.append(options["vertical_char"])
            else:
                bits.append(" ")
        for (field, width) in zip(self._field_names, self._widths):
            if options["fields"] and field not in options["fields"]:
                continue
            if self._header_style == "cap":
                fieldname = field.capitalize()
            elif self._header_style == "title":
                fieldname = field.title()
            elif self._header_style == "upper":
                fieldname = field.upper()
            elif self._header_style == "lower":
                fieldname = field.lower()
            else:
                fieldname = field
            bits.append(" " * lpad + self._justify(fieldname, width, self._align[field]) + " " * rpad)
            if options["border"]:
                if options["vrules"] == ALL:
                    bits.append(options["vertical_char"])
                else:
                    bits.append(" ")
        if options["border"] and options["vrules"] == FRAME:
            bits.pop()
            bits.append(options["vertical_char"])
        if options["border"] and options["hrules"] != NONE:
            bits.append("\n")
            bits.append(self._hrule)
        return "".join(bits)

    def _stringify_row(self, row, options):

        for (index, field, value, width) in zip(range(0, len(row)), self._field_names, row, self._widths):
            # Enforce max widths
            lines = value.split("\n")
            new_lines = []
            for line in lines:
                if _str_block_width(line) > width:
                    line = textwrap.fill(line, width)
                new_lines.append(line)
            lines = new_lines
            value = "\n".join(lines)
            row[index] = value

        row_height = 0
        for c in row:
            h = _get_size(c)[1]
            if h > row_height:
                row_height = h

        bits = []
        lpad, rpad = self._get_padding_widths(options)
        for y in range(0, row_height):
            bits.append([])
            if options["border"]:
                if options["vrules"] in (ALL, FRAME):
                    bits[y].append(self.vertical_char)
                else:
                    bits[y].append(" ")

        for (field, value, width) in zip(self._field_names, row, self._widths):

            valign = self._valign[field]
            lines = value.split("\n")
            d_height = row_height - len(lines)
            if d_height:
                if valign == "m":
                    lines = ([""] * int(d_height / 2) + lines + [""] * (d_height - int(d_height / 2)))
                elif valign == "b":
                    lines = [""] * d_height + lines
                else:
                    lines = lines + [""] * d_height

            y = 0
            for line in lines:
                if options["fields"] and field not in options["fields"]:
                    continue

                bits[y].append(" " * lpad + self._justify(line, width, self._align[field]) + " " * rpad)
                if options["border"]:
                    if options["vrules"] == ALL:
                        bits[y].append(self.vertical_char)
                    else:
                        bits[y].append(" ")
                y += 1

        for y in range(0, row_height):
            if options["border"] and options["vrules"] == FRAME:
                bits[y].pop()
                bits[y].append(options["vertical_char"])

        if options["border"] and options["hrules"] == ALL:
            bits[row_height - 1].append("\n")
            bits[row_height - 1].append(self._hrule)

        for y in range(0, row_height):
            bits[y] = "".join(bits[y])

        return "\n".join(bits)

def _str_block_width(val):
    return wcwidth.wcswidth(_re.sub("", val))
