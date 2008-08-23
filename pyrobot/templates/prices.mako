<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html>
  <head>
  </head>
  <body>
  <form action="/update" method="post">
  <table>
        <tr>
        <td>Id</td>
        <td>Name</td>
        <td>Low price</td>
        <td>High Price</td>
        <td>Active</td>
        <td>Shop Title</td>
        </tr>
    % for iteminfo in c.itemlist:
        <tr>
        <td>${iteminfo.itemId}</td>
        <td>${iteminfo.name}</td>
        <td><input name="${iteminfo.itemId}_low" value="${iteminfo.lowPrice}"></input></td>
        <td><input name="${iteminfo.itemId}_high" value="${iteminfo.highPrice}"></input></td>
        <td><input type="checkbox" name=${iteminfo.itemId}_active
        % if iteminfo.active:
            checked="yes"
        % endif
        ></input></td>
        <td><input name="${iteminfo.itemId}_title" value="${iteminfo.title}" > </input> </td>
        </tr>
        % if str(iteminfo.itemId) in c.pricechecks:
        	% for row in c.pricechecks[str(iteminfo.itemId)]:
        	  <tr><td>${row}</td?</tr>
        	% endfor
      
        % endif
    % endfor
    </table>
    <br>
    <br>
    <input type="submit" value="Submit Changes">
    </form>
    <br>
    <br>
    <form action="/add" method="post">
    Item Id: <input name="itemId" > </input>
    Low Price: <input name="lowPrice" > </input>
    High Price: <input name="highPrice" > </input>
    Title: <input name="title" > </input>
    <input type="submit" value="Add Item">
    </form>
  </body>
</html>
