/*
 * fMBT, free Model Based Testing tool
 * Copyright (c) 2011, Intel Corporation.
 *
 * This program is free software; you can redistribute it and/or modify it
 * under the terms and conditions of the GNU Lesser General Public License,
 * version 2.1, as published by the Free Software Foundation.
 *
 * This program is distributed in the hope it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for
 * more details.
 *
 * You should have received a copy of the GNU Lesser General Public License along with
 * this program; if not, write to the Free Software Foundation, Inc.,
 * 51 Franklin St - Fifth Floor, Boston, MA 02110-1301 USA.
 *
 */
#ifndef __aalang_hh__
#define __aalang_hh__

#include <string>

class aalang {
public:
  virtual void set_name(std::string* name) = 0;
  virtual void set_namestr(std::string* name) = 0;
  virtual void set_variables(std::string* var) = 0;
  virtual void set_istate(std::string* ist) = 0;
  virtual void set_guard(std::string* gua) = 0;
  virtual void set_body(std::string* bod) = 0;
  virtual void set_adapter(std::string* ada) = 0;
  virtual void next_action() = 0;
  virtual std::string stringify() = 0;
protected:
  
};

#endif