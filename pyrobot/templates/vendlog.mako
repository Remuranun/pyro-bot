<% import time %>

<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html>
  <head>
  </head>
  <body>
	<table cellpadding="5">

<% total_buy = 0; total_sell = 0; %>
    % for item in c.vendlog:
	<tr>
	<td>
	% if item.type == 1:
		<font color="green">
		<% total_sell += item.price %>
	% else:
		<font color="red">
		<% total_buy += item.price %>
	% endif
	[${item.itemId}] ${item.name}  </font></td>
	<% context.write('<td>%s</td>'%time.strftime('%m/%d %I:%M %p',item.time)) %>
	<% context.write('<td>%02d</td>'%item.quantity)%>
	<% context.write('<td align="right">%d</td>'%item.price)%>
	</tr>
    % endfor
    </table>
	<br>
	<br>
	<% context.write ( 'Profit: %d'%(total_sell - total_buy)) %>
  </body>
</html>
