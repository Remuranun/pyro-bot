<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html>
  <head>
  </head>
  <body>
  <form action="/update" method="post">
    % for key in c.pricechecks:
        <p>
        ${key} - ${ g.getName(key) }<br>

        % for line in c.pricechecks[key]:
        	${line} <br>
        % endfor
        </p>
    % endfor
  </body>
</html>