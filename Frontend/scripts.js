function readURL(input) {
  if (input.files && input.files[0]) {
    var reader = new FileReader();

    reader.onload = function (e) {
      $('#fileDisplay').show().attr('src', e.target.result);
    };
    document.getElementById('fileName').innerText = input.files[0].name
    reader.readAsDataURL(input.files[0]);
  }
}

function updateTable(object){
var table = document.getElementById("table");
$("#table").find("tr:not(:first)").remove();

var count = 1
for(property in object){
  var row = table.insertRow();
  var pos = row.insertCell(0);
  var name = row.insertCell(1);
  var conf = row.insertCell(2);

  pos.innerHTML = count++;
  name.innerHTML = `${object[property].name}`;
  conf.innerHTML = `${object[property].conf}%`;
}
}

async function uploadFile() {
  var $alert = $('.alert');
  let formData = new FormData();

  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext("2d");

  canvas.width = 28;
  canvas.height = 28;

  ctx.drawImage(fileSelect.files[0], 0, 0, canvas.width, canvas.height);
  const imageBlob = canvas.toBlob();
  console.log(imageBlob.width)

  formData.append("file", imageBlob);
  $.ajax('https://xxlkbgor75nvr7qw256z2xnrdm0ppqai.lambda-url.us-east-2.on.aws/image', {
      method: 'POST',
      data: formData,
      processData: false,
      contentType: false,
              
      success: function (data) {
          $alert.hide();
          document.getElementById('result').innerHTML = data.category
          updateTable(data.confs)
          },
      error: function () {
          $alert.show();
          }
  });
}