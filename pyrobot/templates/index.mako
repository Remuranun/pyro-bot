<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html>
  <head>
  </head>
  <body>
  <h1> Welcome to pyrobot! </h1>
  
  <h2> Current Bots: </h2>
	<table>
	<% bots = h.getBots() %>
  	% for bot in bots:
  	<tr> 
  	<td>
  	${bot}
  	</td>
  	<td>
  	<form action="/control" method="POST">
  		<input type="hidden" name="botname" value="${bot}"</input>
  		<input type="submit" name="start" value="Start"></input>
  		<input type="submit" name="stop" value="Stop"></input>
  	</form>
  	</td>
  	<td>${bots[bot].username}</td>
  	<td>${bots[bot].zeny}</td>
  	<td>${bots[bot].weight}</td>
  	</tr>
  	% endfor
  	</table>
  </body>
</html>
