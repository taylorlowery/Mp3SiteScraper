$("#button-single-file").click(function(){
   $.ajax({
      url: "/singlefile",
       type: "post",
       data: {"test": "single-file"},
       success: function(response){
           console.log(response);
           $("#single-file-response").html(response)
       },
       error: function(xhr) {
          console.log(xhr);
          $("#single-file-response").html(xhr)
       }
   });
});
$("#button-file-range").click(function(){
   $.ajax({
      url: "/filerange",
       type: "post",
       data: {"test": "file-range"},
       success: function(response){
          console.log(response);
          $("#single-file-response").html(response)
       },
       error: function(xhr) {
          console.log(xhr);
          $("#single-file-response").html(xhr)
       }
   });
});
$("#button-all-files").click(function(){
   $.ajax({
      url: "/allfiles",
       type: "post",
       data: {"test": "all-file"},
       success: function(response){
          console.log(response);
          $("#single-file-response").html(response)
       },
       error: function(xhr) {
          console.log(xhr);
          $("#single-file-response").html(xhr)
       }
   });
});